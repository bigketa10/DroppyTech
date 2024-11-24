from django.shortcuts import render
from django.conf import settings
from .forms import ImageUploadForm
from PIL import Image
import imagehash
import os
from annoy import AnnoyIndex
import json
from PIL import Image
import torch.nn as nn
from torchvision import models, transforms
import requests
from io import BytesIO

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

import os
import json
from PIL import Image
from io import BytesIO
import requests
from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse
from torchvision import models, transforms
import torch.nn as nn
from annoy import AnnoyIndex

def nearest_neighbours(query_image_path):
    # Load Annoy index
    annoy_index_path = os.path.join(settings.MEDIA_ROOT, "product_index.ann")
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
        image = Image.open(query_image_path).convert("RGB")
        
        # Apply transformations and get the feature vector
        input_tensor = transform(image).unsqueeze(0)
        query_embedding = model(input_tensor).squeeze(0).detach().numpy()

        # Find the top 5 nearest neighbors
        nearest_neighbors = annoy_index.get_nns_by_vector(query_embedding, 5, include_distances=True)

        results = []
        for neighbor_id, distance in zip(nearest_neighbors[0], nearest_neighbors[1]):
            metadata = id_to_metadata.get(str(neighbor_id), {})
            results.append({
                'neighbor_id': neighbor_id,
                'distance': round(distance, 2),
                'asin': metadata.get('asin'),
                'title': metadata.get('title'),
                'productURL': metadata.get('productURL'),
                'stars': metadata.get('stars'),
                'reviews': metadata.get('reviews'),
                'isBestSeller': metadata.get('isBestSeller'),
                'boughtInLastMonth': metadata.get('boughtInLastMonth'),
                'categoryName': metadata.get('categoryName'),
            })
        return results

    except Exception as e:
        # Log error details for debugging
        print(f"Error in nearest_neighbours: {e}")
        return None


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

            # Perform nearest neighbor search
            nearest_neighbors_results = nearest_neighbours(temp_image_path)

            # Return results as JSON for debugging (can be adapted for rendering)
            if nearest_neighbors_results:
                return render(request, 'image_search/results.html', {'form': form})
            else:
                return JsonResponse({'error': 'Error processing image or finding results'}, status=500)

    else:
        form = ImageUploadForm()


# views.py
from django.conf import settings
from django.shortcuts import render

def results_view(request):
    image_url = '/media/temp_image.jpg'  # Hardcoded for testing
    return render(request, 'image_search/results.html', {'image_url': image_url})

def home_view(request):
    return render(request, 'image_search/home.html')

def search(request):
    return render(request, 'image_search/search.html')
