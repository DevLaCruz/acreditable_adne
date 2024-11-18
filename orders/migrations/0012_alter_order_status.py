# Generated by Django 5.0.7 on 2024-11-12 17:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0011_alter_order_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('Accepted', 'Aceptado'), ('Canceled', 'Cancelado'), ('New', 'Nuevo'), ('Completred', 'Completado')], default='New', max_length=50),
        ),
    ]