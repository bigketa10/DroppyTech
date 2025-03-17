from PIL import Image, ImageChops
img1, img2 = Image.open('image1.jpg'), Image.open('image2.jpg')
diff = ImageChops.difference(img1, img2)

if diff.getbbox():
    diff.show()
else:
    print('Images are identical')