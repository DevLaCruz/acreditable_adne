import hashlib
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.safestring import mark_safe
from accounts.models import Account


def generate_hash_id(instance_id):
    """Genera un hash SHA-256 basado en el ID de la instancia."""
    hash_input = f"{instance_id}".encode('utf-8')
    return hashlib.sha256(hash_input).hexdigest()


class Client(models.Model):
    """
    Representa a la persona / cliente con su información personal,
    contacto, dirección y coordenadas GPS para la ruta de cobro.
    """
    user = models.OneToOneField(Account, on_delete=models.SET_NULL, blank=True, null=True, related_name='client_profile', verbose_name="Cuenta de Usuario Ecommerce")
    know_name = models.CharField(max_length=150, verbose_name="Nombre Completo / Conocido")
    phone_number = models.CharField(max_length=30, blank=True, verbose_name="Teléfono / Celular / WhatsApp")
    address = models.TextField(blank=True, verbose_name="Dirección de Domicilio")
    sector = models.CharField(max_length=100, blank=True, help_text="Ej: Sector Brinos, P.J. Santos Chocano, J.L. Ortiz", verbose_name="Sector / Zona")
    latitude = models.FloatField(blank=True, null=True, verbose_name="Latitud GPS")
    longitude = models.FloatField(blank=True, null=True, verbose_name="Longitud GPS")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha Registro")
    hash_id = models.CharField(max_length=255, unique=True, blank=True, editable=False)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['-id']

    def __str__(self):
        if self.user:
            return f"{self.user.first_name} {self.user.last_name} ({self.know_name or self.user.email})"
        return self.know_name or f"Cliente #{self.id}"

    @property
    def total_balance(self):
        """Devuelve la suma del saldo pendiente de todas sus tarjetas activas."""
        return sum(card.balance for card in self.debt_cards.filter(status='active'))

    @property
    def total_debt(self):
        """Devuelve el total contratado original de sus tarjetas activas."""
        return sum(card.total_amount for card in self.debt_cards.filter(status='active'))

    @property
    def active_cards_count(self):
        return self.debt_cards.filter(status='active').count()

    @property
    def map_url(self):
        if self.latitude and self.longitude:
            return f"https://www.google.com/maps/search/?api=1&query={self.latitude},{self.longitude}"
        return None

    def view_on_map(self):
        if self.latitude and self.longitude:
            return mark_safe(f'<a href="{self.map_url}" target="_blank" class="button" style="background:#2563eb; color:white; padding:4px 8px; border-radius:4px; text-decoration:none;">📍 Ver en mapa</a>')
        return "Sin ubicación GPS"

    view_on_map.short_description = "Ubicación GPS"

    def save(self, *args, **kwargs):
        if not self.hash_id:
            hash_input = f"{self.know_name}{self.address}{self.latitude}{self.longitude}".encode('utf-8')
            self.hash_id = hashlib.sha256(hash_input).hexdigest()
        super().save(*args, **kwargs)


class DebtCard(models.Model):
    """
    Representa la Tarjeta o Ficha de Crédito de Cobranza (Ej. Tarjeta #46).
    Registra el monto total de la venta a crédito, el saldo restante y
    los acuerdos de cuota (semanal, quincenal o mensual).
    """
    FREQUENCY_CHOICES = [
        ('S', 'Semanal'),
        ('Q', 'Quincenal'),
        ('M', 'Mensual'),
    ]

    STATUS_CHOICES = [
        ('active', 'Activa (En cobro)'),
        ('paid', 'Cancelada / Pagada'),
        ('overdue', 'Vencida'),
        ('closed', 'Cerrada / Anulada'),
    ]

    card_number = models.CharField(max_length=50, unique=True, verbose_name="Nº de Tarjeta / Ficha")
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='debt_cards', verbose_name="Cliente")
    article_description = models.CharField(max_length=255, verbose_name="Artículo(s) comprados", help_text="Ej: 1 Multiuso Melamine x 160")
    
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Monto Total Deuda (S/)")
    balance = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Saldo Restante (S/)")
    
    # Modalidad y Cuota Pactada (Valores S, Q, M al pie de la tarjeta)
    payment_frequency = models.CharField(max_length=1, choices=FREQUENCY_CHOICES, default='S', verbose_name="Frecuencia de Pago Pactada")
    agreed_quota = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Cuota Pactada (S/)")

    collector = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='collected_cards', verbose_name="Cobrador Asignado")
    start_date = models.DateField(verbose_name="Fecha de Emisión / Venta")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name="Estado de Deuda")
    hash_id = models.CharField(max_length=255, unique=True, blank=True, editable=False)

    class Meta:
        verbose_name = "Tarjeta de Deuda"
        verbose_name_plural = "Tarjetas de Deudas"
        ordering = ['-id']

    def __str__(self):
        return f"Tarjeta #{self.card_number} - {self.client.know_name} (Resta: S/ {self.balance})"

    def recalculate_balance(self):
        """Recalcula el saldo restante acumulando los pagos registrados."""
        total_paid = sum(p.amount for p in self.payments.all())
        self.balance = self.total_amount - total_paid
        if self.balance <= 0:
            self.balance = 0
            self.status = 'paid'
        elif self.status == 'paid' and self.balance > 0:
            self.status = 'active'
        self.save()


class DebtPayment(models.Model):
    """
    Cada abono/pago registrado en las casillas de la tarjeta física (FECHA | PAGO | RESTA).
    """
    card = models.ForeignKey(DebtCard, on_delete=models.CASCADE, related_name='payments', verbose_name="Tarjeta de Deuda")
    payment_date = models.DateField(verbose_name="Fecha del Pago")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Monto Pagado (S/)")
    balance_after = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Saldo Restante (Resta S/)")
    collector = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Cobrador que Recibió")
    notes = models.CharField(max_length=255, blank=True, verbose_name="Observaciones / Notas")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Pago de Cuota"
        verbose_name_plural = "Pagos de Cuotas"
        ordering = ['payment_date', 'created_at']

    def __str__(self):
        return f"Pago S/ {self.amount} en {self.payment_date} (Tarjeta #{self.card.card_number})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.card.recalculate_balance()


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
    hash_id = models.CharField(max_length=255, unique=True, blank=True, editable=False)

    def __str__(self):
        return f"{self.debtor_name} - {self.account_number}"


# =========================================================
# VINCULACIÓN AUTOMÁTICA PRECISA (Self-Service Matching)
# =========================================================

@receiver(post_save, sender=Account)
def auto_link_client_on_user_creation(sender, instance, created, **kwargs):
    """
    Cuando un usuario se registra en la web (Ecommerce), si su teléfono o email
    coincide con un Cliente registrado previamente en campo, los vincula automáticamente.
    """
    if created:
        matching_client = None
        if instance.phone_number:
            matching_client = Client.objects.filter(phone_number=instance.phone_number, user__isnull=True).first()
        if not matching_client and instance.email:
            matching_client = Client.objects.filter(user__isnull=True).filter(
                models.Q(know_name__icontains=instance.first_name) & models.Q(know_name__icontains=instance.last_name)
            ).first()
            
        if matching_client:
            matching_client.user = instance
            matching_client.save(update_fields=['user'])


@receiver(post_save, sender=Client)
def auto_link_user_on_client_creation(sender, instance, created, **kwargs):
    """
    Cuando un cobrador registra un Cliente en campo con su teléfono, si ese teléfono
    ya pertenece a una cuenta Ecommerce registrada en el sistema, los vincula automáticamente.
    """
    if created and not instance.user and instance.phone_number:
        matching_user = Account.objects.filter(phone_number=instance.phone_number).first()
        if matching_user:
            instance.user = matching_user
            instance.save(update_fields=['user'])


@receiver(post_save, sender=Client)
def set_client_hash_id(sender, instance, created, **kwargs):
    if created and not instance.hash_id:
        instance.hash_id = generate_hash_id(instance.id)
        instance.save(update_fields=['hash_id'])


@receiver(post_save, sender=DebtCard)
def set_debtcard_hash_id(sender, instance, created, **kwargs):
    if created and not instance.hash_id:
        instance.hash_id = generate_hash_id(instance.id)
        instance.save(update_fields=['hash_id'])
