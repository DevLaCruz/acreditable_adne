# Generated manually - adds max_length=255 to Product.images
# Fixes StringDataRightTruncation in PostgreSQL when image paths exceed 100 chars

from django.db import migrations, models

import store.models


class Migration(migrations.Migration):
    dependencies = [
        ("store", "0010_alter_product_images_alter_productgallery_image"),
    ]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="images",
            field=models.ImageField(
                max_length=255,
                upload_to=store.models.product_image_path,
            ),
        ),
    ]
