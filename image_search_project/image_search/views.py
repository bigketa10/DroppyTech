from django.shortcuts import render
from django.conf import settings
from .forms import ImageUploadForm
import os

def search_view(request):
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Handle image upload
            uploaded_image = form.cleaned_data['image']

            # Save the uploaded image to the media folder
            temp_image_path = os.path.join(settings.MEDIA_ROOT, 'temp_image.jpg')
            with open(temp_image_path, 'wb+') as destination:
                for chunk in uploaded_image.chunks():
                    destination.write(chunk)

            # Check if the file was saved
            file_exists = os.path.isfile(temp_image_path)
            if not file_exists:
                return render(request, 'image_search/search.html', {'error': 'File could not be saved.'})

            # Proceed with image processing and comparison here...
            return render(request, 'image_search/results.html', {'image_path': temp_image_path})

    else:
        form = ImageUploadForm()

    return render(request, 'image_search/search.html', {'form': form})
