
from django.core.exceptions import ValidationError
import os

# def allow_only_images_validator():
#     ext = os.path.splitext(value.name)[1] #cover-image.jpg
#     print(ext)
#     valid_extensions = ['.png', '.jpg' '.jpeg']
#     if not ext.lower() in valid_extensions:
#         raise ValidationError('Niet-ondersteunde bestandsextensie. Toegestane extensies:' + str(valid_extensions))