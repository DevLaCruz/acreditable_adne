# Generated by Django 5.0.7 on 2024-12-30 06:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0014_alter_order_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('Canceled', 'Cancelado'), ('New', 'Nuevo'), ('Accepted', 'Aceptado'), ('Completred', 'Completado')], default='New', max_length=50),
        ),
    ]
