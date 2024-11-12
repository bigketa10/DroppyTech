from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(null=True,blank=True,upload_to='media/products/')
    venue_image = models.ImageField(null=True,blank=True,upload_to='media/products/')

    def __str__(self):
        return self.name

