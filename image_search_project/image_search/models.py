from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=100)       # A short text field for product names
    description = models.TextField()              # A text field for longer descriptions
    price = models.DecimalField(max_digits=10, decimal_places=2)  # A decimal field for prices
    image = models.ImageField(null=True,blank=True,upload_to='media/products/')
    venue_image = models.ImageField(null=True,blank=True,upload_to='media/products/')
    created_at = models.DateTimeField(auto_now_add=True)  # Auto-populated timestamp when created
    updated_at = models.DateTimeField(auto_now=True)      # Auto-populated timestamp when updated

    def __str__(self):
        return self.name


