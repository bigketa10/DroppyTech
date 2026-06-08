# Droppy: Dropshipping Detection Web App

---

## About the Project
Droppy is a Django-based web application designed to help consumers spot dropshipped items by scanning the web for products that use the exact same stock photos. Dropshippers often use uniform, white-background product photos provided by third-party suppliers. By analyzing these images across major retailers like Amazon, eBay, and AliExpress, this tool helps users identify potentially low-quality dropshipped goods, avoid long delivery times, and find the best direct prices.


## Key Features
* **Versatile Image Inputs:** Users can search the database by uploading an image file directly from their device, pasting an image URL, or providing a direct link to an Amazon Product Page.
* **Perceptual Hashing & Similarity Scoring:** The application converts images into grayscale, resizes them, and generates a binary perceptual hash (phash). It then calculates the Hamming distance between hashes to return a percentage-based similarity score (from 0% to 100%) to determine how closely two products match.
* **Deep Learning Feature Extraction:** Leverages a pre-trained ResNet-18 convolutional neural network (via PyTorch) with its fully connected layer removed to extract 512-dimensional feature vectors from images.
* **Vector Database Indexing:** Utilizes the Spotify ANNOY (Approximate Nearest Neighbors Oh Yeah) library to build a memory-efficient index of image vectors, allowing for rapid similarity searches to generate a visual grid of the 24 "nearest neighbor" products.
* **Automated Web Scraping:** Integrates `BeautifulSoup` to automatically parse HTML and extract key product details—such as price, product name, image URLs, and dispatch origin—from Amazon pages.
* **Responsive UI:** Features a clean, intuitive user interface built with HTML5 and Bootstrap 5. The frontend includes a navigation bar, a dark-mode-friendly design, and an easy-to-use search page.

## Technology Stack
* **Backend Framework:** Django (Python)
* **Machine Learning & Computer Vision:** PyTorch (ResNet-18), ANNOY, Python Imaging Library (PIL), `imagehash`
* **Web Scraping:** `BeautifulSoup4`, `requests`
* **Data Handling:** Pandas (for processing CSV datasets)
* **Frontend:** HTML5, CSS, Bootstrap 5

## System Requirements
* **Supported OS:** Windows, macOS, iOS, or Android.
* **Browser:** Any modern web browser (Google Chrome, Mozilla Firefox, Microsoft Edge, etc.).
* **Hardware (User):** A device with at least 1GB of RAM, 10MB of available secondary storage space, and an active internet connection.
* **Hardware (Development):** A strong computer capable of running image processing models and a local web server simultaneously.

## Setup and Installation (Development)
To run this project locally for development and testing, follow these steps:

1. **Initialize the Django Environment:** Create the project directory by running `py -m django-admin startproject image_search_project`.
2. **Navigate to the Directory:** Change your working directory using `cd image_search_project`.
3. **Start the App:** Create the specific search application by running `py -m django startapp image_search`.
4. **Install Dependencies:** Ensure you have the required Python libraries installed, including `django`, `requests`, `bs4` (BeautifulSoup), `PIL` (Pillow), `imagehash`, `torch`, `torchvision`, and `annoy`.
5. **Run the Server:** Start the Django development server by executing `py -m manage runserver`.
6. **Access the App:** Open your web browser and navigate to `http://127.0.0.1:8000/` to view the project.
