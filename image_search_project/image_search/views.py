import os
import json
import requests
from io import BytesIO
from bs4 import BeautifulSoup
from PIL import Image
import imagehash
from annoy import AnnoyIndex
import torch.nn as nn
from torchvision import models, transforms

from django.conf import settings
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import JsonResponse

from .forms import ImageUploadForm

# from cairosvg import svg2png
# os.environ['path'] += r';C:\Users\bisha\AppData\Local\Programs\Python\Python312\cairo\dlls'
# def convert_from_svg_to_jpg(image):
#     temp_jpg_path = os.path.join(settings.MEDIA_ROOT, 'temp_image.jpg')
#     temp_png_path = temp_jpg_path.replace('temp_image.jpg', 'temp_image.png')
#     svg2png(bytestring=image,write_to=temp_png_path)
#     #open image in png format 
#     img_png = Image.open(temp_png_path) 
#     #The image object is used to save the image in jpg format
#     img_png.save(temp_jpg_path)

def get_amazon_product_details(url):
    try:
        # Headers to mimic a real user and reduce chances of being blocked by Amazon
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/83.0.4103.116 Safari/537.36'
            )
        }

        # Send request to the URL
        response = requests.get(url, headers=headers)
        response.raise_for_status() # Raises an error if the request fails (e.g., 404 or 500)

        # Parse the HTML content of the response using BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract product details safely
        currency_element = soup.find(class_='a-price-symbol')
        price_whole_element = soup.find(class_='a-price-whole')
        price_fraction_element = soup.find(class_='a-price-fraction')
        image_element = soup.find(id='landingImage')
        name_element = soup.find(id='productTitle')

        # Assign values only if elements exist to prevent AttributeError
        currency = currency_element.get_text().strip() if currency_element else ''
        price_whole = price_whole_element.get_text().strip() if price_whole_element else '0'
        price_fraction = price_fraction_element.get_text().strip() if price_fraction_element else '00'
        
        price = f'{currency}{price_whole}.{price_fraction}'
        image_url = image_element['src'] if image_element else 'No image found'
        name = name_element.get_text().strip() if name_element else 'No name found'

        print ('Price: ', price)
        print ('Image URL: ', image_url)   
        print ('Name: ', name)

        return {
            'name': name,
            'price': price,
            'image_url': image_url
        }
    
    # Handle exceptions
    except requests.exceptions.RequestException as e:
        print(f'Network error: {e}')
        return {'error': 'Network error or blocked request'}
    except Exception as e:
        print(f'Error fetching product details: {e}')
        return {'error': 'Parsing error or missing product details'}

def dispatch(url):
    try:
        # Headers to mimic a real user and reduce chances of being blocked by Amazon
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/83.0.4103.116 Safari/537.36'
            )
        }

        # Send request to the URL
        response = requests.get(url, headers=headers)
        response.raise_for_status() # Raises an error if the request fails (e.g., 404 or 500)

        # Parse the HTML content of the response using BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract product details safely
        dispatch_from = soup.find(class_='a-size-small offer-display-feature-text-message')

        # Assign values only if elements exist to prevent AttributeError
        dispatch_from = dispatch_from.get_text().strip() if dispatch_from else 'Unknown'

        return dispatch_from
    
    # Handle exceptions
    except requests.exceptions.RequestException as e:
        print(f'Network error: {e}')
        return 'Unknown'
    except Exception as e:
        print(f'Error fetching product details: {e}')
        return 'Unknown'

# Compute the Hamming distance between two hashes
def compute_hamming_distance(hash1, hash2):
    return bin(int(hash1, 16) ^ int(hash2, 16)).count('1')

# Compare two images and compute Hamming distance and similarity
def compare_image(image_path1, image_path2):
    img1 = Image.open(image_path1)
    img2 = Image.open(image_path2)

    # Generate perceptual hashes for both images
    hash1 = imagehash.phash(img1)
    hash2 = imagehash.phash(img2)

    # Calculate Hamming distance
    hamming_distance = compute_hamming_distance(hash1.hash.flatten().tobytes().hex(), hash2.hash.flatten().tobytes().hex())

    # Calculate similarity (1 - normalized Hamming distance)
    max_length = max(len(hash1.hash.flatten()), len(hash2.hash.flatten()))
    similarity = 1 - hamming_distance / max_length
    return hamming_distance, similarity

def nearest_neighbors(query_image_path):
    # Load Annoy index
    annoy_index_path = os.path.join(settings.MEDIA_ROOT, 'product_index (2).ann')
    annoy_index = AnnoyIndex(512, 'angular')
    annoy_index.load(annoy_index_path)

    # Load metadata mapping
    metadata_path = os.path.join(settings.MEDIA_ROOT, 'id_to_metadata.json')
    with open(metadata_path, 'r') as f:
        id_to_metadata = json.load(f)

    # Load ResNet18 model
    weights = models.ResNet18_Weights.IMAGENET1K_V1
    model = models.resnet18(weights=weights)
    model.fc = nn.Identity()
    model.eval()

    # Transformation pipeline with explicit normalization
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),  # Fixed normalization
    ])
    
    try:
        # Open the image and ensure it's in RGB
        image = Image.open(query_image_path).convert('RGB')
        
        # Apply transformations and get the feature vector
        input_tensor = transform(image).unsqueeze(0)
        query_embedding = model(input_tensor).squeeze(0).detach().numpy()

        # Find the top 5 nearest neighbors
        nearest_neighbors = annoy_index.get_nns_by_vector(query_embedding, 32, include_distances=True)

        results = []
        
        for neighbor_id, distance in zip(nearest_neighbors[0], nearest_neighbors[1]):
            metadata = id_to_metadata.get(str(neighbor_id), {})
            results.append({
                'neighbor_id': neighbor_id,
                'distance': round(distance, 2),
                'asin': convert_from_zero(metadata.get('asin')),
                'price': '£' + str(metadata.get('price')),
                'imgUrl': convert_from_zero(metadata.get('imgUrl')),
                'title': convert_from_zero(metadata.get('title')),
                'productURL': convert_from_zero(metadata.get('productURL')),
                'stars': convert_from_zero(metadata.get('stars')),
                'reviews': convert_from_zero(metadata.get('reviews')),
                'isBestSeller': metadata.get('isBestSeller'),
                'boughtInLastMonth': metadata.get('boughtInLastMonth'),
                'categoryName': metadata.get('categoryName'),
                'dispatchFrom': (dispatch(metadata.get('productURL'))),
            })
        return results

    # Log error details for debugging
    except Exception as e:
        print(f'Error in nearest_neighbors: {e}')
        return None
    
def link_convert(url):
    try:
        # Headers to mimic a real user and reduce chances of being blocked by Amazon
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/83.0.4103.116 Safari/537.36'
            )
        }

        # Send the request to the URL
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error if the request fails

        # Parse the page content
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract product details
        image_url = soup.find(id='landingImage')['src']
        return image_url
    
    # Log error details for debugging
    except Exception as e:
        print(f'Error fetching product details: {e}')
        return 'Unavailable'

def search_view(request):
    if request.method == 'POST':
        image_url = request.POST.get('image_url')  # URL input
        image_url= image_url.strip()
        uploaded_image = request.FILES.get('image')  # File input
        temp = image_url
        if image_url:
            try:
                try:
                    # Convert the URL to image URL it's an Amazon product URL
                    image_url = link_convert(image_url)
                    image_url= image_url.strip()
                    response = requests.get(image_url, stream=True)
                    print(f'Testing:{image_url}')

                    if response.status_code == 200:
                        temp_image_path = os.path.join(settings.MEDIA_ROOT, 'temp_image.jpg')
                        with open(temp_image_path, 'wb+') as f:

                            for chunk in response.iter_content(1024):
                                f.write(chunk)
                    results = nearest_neighbors(temp_image_path)
                    print(results)
                    if results == None:
                        return render(request, 'image_search/search.html', {'error': 'Error fetching image.'})
                    request.session['search_results'] = results
                    return redirect(reverse('results'))

                except:
                    # Converts it back into the original URL if it was already an image URL
                    image_url = temp
                    response = requests.get(image_url, stream=True)
                    print(f'Testing:{image_url}')

                    if response.status_code == 200:
                        temp_image_path = os.path.join(settings.MEDIA_ROOT, 'temp_image.jpg')
                        with open(temp_image_path, 'wb+') as f:
                            for chunk in response.iter_content(1024):

                                f.write(chunk)
                    results = nearest_neighbors(temp_image_path)
                    if results == None:
                        return render(request, 'image_search/search.html', {'error': 'Error fetching image.'})
                    request.session['search_results'] = results
                    return redirect(reverse('results'))

            except Exception as e:
                return render(request, 'image_search/search.html', {'error': f'Error fetching image: {e}'})

        elif uploaded_image:
            temp_image_path = os.path.join(settings.MEDIA_ROOT, 'temp_image.jpg')
            with open(temp_image_path, 'wb+') as f:

                for chunk in uploaded_image.chunks():
                    f.write(chunk)

            results = nearest_neighbors(temp_image_path)
            if results == None:
                return render(request, 'image_search/search.html', {'error': 'Error fetching image.'})
            request.session['search_results'] = results
            return redirect(reverse('results'))

        # If neither input is provided
        return render(request, 'image_search/search.html', {'error': 'Please provide an image or image URL.'})

    return render(request, 'image_search/search.html')

from django.http import JsonResponse
import urllib.parse

def url_search(request, url):
    decoded_url = urllib.parse.unquote(url) # Decode the URL
    image_url = url  # URL input
    image_url= image_url.strip()
    temp = image_url
    if image_url:
        try:
            try:
                # Convert the URL to image URL it's an Amazon product URL
                image_url = link_convert(image_url)
                image_url= image_url.strip()
                response = requests.get(image_url, stream=True)
                print(f'Testing:{image_url}')

                if response.status_code == 200:
                    temp_image_path = os.path.join(settings.MEDIA_ROOT, 'temp_image.jpg')
                    with open(temp_image_path, 'wb+') as f:

                        for chunk in response.iter_content(1024):
                            f.write(chunk)
                results = nearest_neighbors(temp_image_path)
                print(results)
                if results == None:
                    return render(request, 'image_search/search.html', {'error': 'Error fetching image.'})
                request.session['search_results'] = results
                return redirect(reverse('results'))

            except:
                # Converts it back into the original URL if it was already an image URL
                image_url = temp
                response = requests.get(image_url, stream=True)
                print(f'Testing:{image_url}')

                if response.status_code == 200:
                    temp_image_path = os.path.join(settings.MEDIA_ROOT, 'temp_image.jpg')
                    with open(temp_image_path, 'wb+') as f:
                        for chunk in response.iter_content(1024):

                            f.write(chunk)
                results = nearest_neighbors(temp_image_path)
                if results == None:
                    return render(request, 'image_search/search.html', {'error': 'Error fetching image.'})
                request.session['search_results'] = results
                return redirect(reverse('results'))

        except Exception as e:
            return render(request, 'image_search/search.html', {'error': f'Error fetching image: {e}'})
    return render(request, 'image_search/search.html')

def convert_from_zero(value):
    if value == 0:
        return 'N/A'
    return value
def results_view(request):
    results = request.session.get('search_results', [])
    return render(request, 'image_search/results.html', {'results': results})

def home_view(request):
    return render(request, 'image_search/home.html')

def search(request):
    return render(request, 'image_search/search.html')