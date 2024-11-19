from django.shortcuts import render
from django.conf import settings
from .forms import ImageUploadForm
from PIL import Image
import imagehash
import os

# Compute the Hamming distance between two hashes
def compute_hamming_distance(hash1, hash2):
    return bin(int(hash1, 16) ^ int(hash2, 16)).count('1')

# Compare two images and compute Hamming distance and similarity
def compare_images(image_path1, image_path2):
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

# Main view for handling image upload and comparison
def search_view(request):
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_image = form.cleaned_data['image']
            temp_image_path = os.path.join(settings.MEDIA_ROOT, 'temp_image.jpg')

            # Save the uploaded image temporarily
            with open(temp_image_path, 'wb+') as destination:
                for chunk in uploaded_image.chunks():
                    destination.write(chunk)

            # Iterate through existing images in 'products/' directory
            products_dir = os.path.join(settings.MEDIA_ROOT, 'products')
            product_images = os.listdir(products_dir)
            results = []

            for image_file in product_images:
                product_image_path = os.path.join(products_dir, image_file)
                hamming_distance, similarity = compare_images(temp_image_path, product_image_path)

                results.append({
                    'image_name': image_file,
                    'hamming_distance': hamming_distance,
                    'similarity': round(similarity * 100, 2)  # similarity as a percentage
                })

            return render(request, 'image_search/results.html', {'results': results})

    else:
        form = ImageUploadForm()

    return render(request, 'image_search/search.html', {'form': form})

def upload_image_view(request):
    if request.method == 'POST' and request.FILES['image']:
        image = request.FILES['image']
        image_name = 'temp_image.jpg'  # Always save as 'temp_image.jpg'
        image_path = os.path.join(settings.MEDIA_ROOT, image_name)

        # Save the uploaded image
        with open(image_path, 'wb+') as destination:
            for chunk in image.chunks():
                destination.write(chunk)

        # Pass results to the template
        results = perform_comparison(image_path)  # Your image comparison logic
        return render(request, 'template_name.html', {
            'results': results,
        })

    return render(request, 'upload.html')

# views.py
from django.conf import settings
from django.shortcuts import render

def results_view(request):
    image_url = '/media/temp_image.jpg'  # Hardcoded for testing
    print("Debug: Hardcoded image URL:", image_url)  # Debugging line
    return render(request, 'image_search/results.html', {'image_url': image_url})

def home_view(request):
    return render(request, 'image_search/home.html')

def search(request):
    return render(request, 'image_search/search.html')
