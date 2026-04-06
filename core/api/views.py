from rest_framework import viewsets, status
from rest_framework.response import Response
from django.db import transaction
from core.mixins import SoftDeleteMixin, HistoryMixin


class CoreModelViewSet(SoftDeleteMixin, HistoryMixin, viewsets.ModelViewSet):
    """
    Base ViewSet que combina soft delete y registro de historial, 
    permite inserciones individuales y masivas.
    """

    def create(self, request, *args, **kwargs):
        is_bulk = isinstance(request.data, list)
        serializer = self.get_serializer(data=request.data, many=is_bulk)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            instances = serializer.save()
            created_ids = [str(instance.pk) for instance in instances] if is_bulk else [str(instances.pk)]

            # Pasar el objeto request completo a get_related_fields
            related_fields = self.get_related_fields(request, is_bulk)

            # Registrar historial
            self.log_history(
                request,
                action_summary=self.get_action_summary("create", created_ids),
                related_fields=related_fields,
            )

        return Response(serializer.data, status=status.HTTP_201_CREATED)



    def update(self, request, *args, **kwargs):
        """
        Actualiza un registro y registra la acción en el historial.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            updated_instance = serializer.save()
            self.log_history(
                request,
                action_summary=self.get_action_summary("update", updated_instance),
                related_fields=self.get_related_fields(request, updated_instance),
            )
        return Response(serializer.data)

    def get_action_summary(self, action, created_ids):
        model_name = self.get_serializer().Meta.model.__name__
        count = len(created_ids)
        ids_str = ", ".join(created_ids[:10])
        if len(created_ids) > 10:
            ids_str += ", ..."
        return f"{action.capitalize()} {count} {model_name}(s): IDs {ids_str}"

    def get_related_fields(self, data, is_bulk):
        """
        Método abstracto que debe sobrescribirse en vistas específicas.
        """
        return {}
