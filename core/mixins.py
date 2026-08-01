from rest_framework.response import Response
from rest_framework import status
from django.apps import apps
from django.utils.timezone import now

class SoftDeleteMixin:
    def destroy(self, request, *args, **kwargs):
        """
        Marca el registro como eliminado en lugar de eliminarlo físicamente.
        """
        instance = self.get_object()
        user = request.user if request.user.is_authenticated else None
        instance.delete(user=user)  # Llama al método delete del modelo
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self):
        """
        Devuelve solo los registros activos (no eliminados).
        """
        return super().get_queryset().filter(is_deleted=False)

class HistoryMixin:

    def log_history(self, request, action_summary, related_fields=None):
        """
        Registra una acción en el historial con username o email y campos relacionados.
        """
        HistoryModel = self.get_history_model()
        if HistoryModel:
            user = request.user if request.user.is_authenticated else None
            username_or_email = user.username if hasattr(user, "username") and user.username else user.email

            history_data = {
                "idUser": user,
                "action": f"{username_or_email} - {action_summary}",
                "created_at": now(),
            }

            if related_fields:
                history_data.update(related_fields)

            return HistoryModel.objects.create(**history_data)
        return None


    def get_history_model(self):
        """
        Retorna dinámicamente el modelo de historial según el modelo base.
        """
        app_label = self.get_serializer().Meta.model._meta.app_label
        history_model_name = "History"
        try:
            return apps.get_model(app_label, history_model_name)
        except LookupError:
            return None


