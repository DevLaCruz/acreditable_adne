# Generated by Django 5.0.7 on 2024-11-12 17:57

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0005_auto_20230905_1317'),
    ]

    operations = [
        migrations.CreateModel(
            name='VariationCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
            ],
        ),
        migrations.AlterField(
            model_name='variation',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variations', to='store.product'),
        ),
        migrations.AlterField(
            model_name='variation',
            name='variation_category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variations', to='store.variationcategory'),
        ),
        migrations.AlterUniqueTogether(
            name='variation',
            unique_together={('product', 'variation_category', 'variation_value')},
        ),
    ]