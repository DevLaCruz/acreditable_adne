#from django.contrib.gis.db import models as gis_models
#from django.contrib.gis.geos import Point
from django.db import models
from django.urls import reverse
from django.utils.html import mark_safe
from accounts.models import Account
import hashlib
from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import Account

# Intentamos usar GIS si está disponible
# try:
#     from django.contrib.gis.db import models as gis_models
#     GIS_ENABLED = True
# except ImportError:
#     GIS_ENABLED = False


class Client(models.Model):
    user = models.OneToOneField(Account, on_delete=models.CASCADE, blank=True, null=True)
    know_name = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    hash_id = models.CharField(max_length=255, unique=True, blank=True, editable=False)

    def __str__(self):
        if self.user:
            return f"{self.user.first_name} {self.user.last_name} ({self.user.email})"
        return self.know_name

    @property
    def map_url(self):
        if self.latitude and self.longitude:
            return f"https://www.google.com/maps/search/?api=1&query={self.latitude},{self.longitude}"
        return None

    def view_on_map(self):
        if self.latitude and self.longitude:
            from django.utils.safestring import mark_safe
            return mark_safe(f'<a href="{self.map_url}" target="_blank">Ver en mapa</a>')
        return "Sin ubicación"

    view_on_map.short_description = "Mapa"

    def save(self, *args, **kwargs):
        if not self.hash_id:
            # Generar un hash único basado en los datos del cliente
            hash_input = f"{self.know_name}{self.address}{self.latitude}{self.longitude}".encode('utf-8')
            self.hash_id = hashlib.sha256(hash_input).hexdigest()
        super().save(*args, **kwargs)


# Create your models here.
class DebtAccount(models.Model):
    account_number = models.CharField(max_length=20, unique=True)
    debtor_name = models.CharField(max_length=100)
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=[('active', 'Active'), ('closed', 'Closed')],
        default='active'
    )
    hash_id = models.CharField(max_length=255, unique=True, blank=True, editable=False)  # <-- AGREGA ESTO

    def __str__(self):
        return f"{self.debtor_name} - {self.account_number}"




# signals.py (o al final de tu models.py si prefieres)
def generate_hash_id(instance_id):
    """Genera un hash SHA-256 basado en el ID de la instancia."""
    hash_input = f"{instance_id}".encode('utf-8')
    return hashlib.sha256(hash_input).hexdigest()

@receiver(post_save, sender=Client)
def set_client_hash_id(sender, instance, created, **kwargs):
    if created and not instance.hash_id:
        instance.hash_id = generate_hash_id(instance.id)
        instance.save(update_fields=['hash_id'])

@receiver(post_save, sender=DebtAccount)
def set_debtaccount_hash_id(sender, instance, created, **kwargs):
    if created and not instance.hash_id:
        instance.hash_id = generate_hash_id(instance.id)
        instance.save(update_fields=['hash_id'])

