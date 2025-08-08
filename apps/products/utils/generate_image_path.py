import os

from django.utils.text import slugify


def product_image_upload_path(instance, filename):
    # Access the product's name safely
    product = instance.product
    folder_name = slugify(product.name) if product else 'unassigned'
    return os.path.join('product-images', folder_name, filename)