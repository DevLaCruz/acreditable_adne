from django.db import models
from django.utils import timezone
from django.conf import settings


# Manager personalizado para Soft Delete
class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        # Excluye registros eliminados por defecto
        return super().get_queryset().filter(is_deleted=False)


# Modelo Base para Soft Delete
class CoreModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deleted_%(class)s_set",
        verbose_name="Eliminado por",
    )

    # Managers
    objects = SoftDeleteManager()  # Solo registros activos
    all_objects = models.Manager()  # Incluye registros eliminados

    def delete(self, *args, user=None, **kwargs):
        """
        Marca el registro como eliminado (Soft Delete).
        """
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save()

    def restore(self, *args, **kwargs):
        """
        Restaura un registro eliminado.
        """
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save()

    class Meta:
        abstract = True


# Manager para manejar consultas en el historial
class CoreHistoryManager(SoftDeleteManager):
    def filter_by_user(self, user):
        """
        Filtra los registros del historial por usuario.
        """
        return self.get_queryset().filter(idUser=user)

    def filter_by_date(self, start_date, end_date):
        """
        Filtra los registros del historial en un rango de fechas.
        """
        return self.get_queryset().filter(created_at__range=(start_date, end_date))


# Modelo Base para el Historial
class CoreHistory(CoreModel):
    idUser = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Usuario",
    )
    action = models.TextField(verbose_name="Acción realizada")

    # Manager específico
    objects = CoreHistoryManager()

    def format_action(self):
        """
        Genera una representación personalizada del historial.
        Sobrescribir en modelos específicos.
        """
        user_info = f"{self.idUser.email}" if self.idUser else "Usuario desconocido"
        return f"{user_info} - {self.action}"

    def __str__(self):
        return self.format_action()

    class Meta:
        abstract = True
