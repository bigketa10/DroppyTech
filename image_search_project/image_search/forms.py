from django import forms

class ImageUploadForm(forms.Form):
    image = forms.ImageField()
    
#class LinkUploadForm(forms.Form):
#    link = forms.URLField()