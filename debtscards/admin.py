from django.contrib import admin
from .models import Client, DebtAccount


class ClientAdmin(admin.ModelAdmin):
    list_display = ('know_name', 'user', 'latitude', 'longitude', 'hash_id', 'view_on_map')
    readonly_fields = ('hash_id', 'view_on_map')
    search_fields = ('know_name', 'user__email', 'user__first_name', 'user__last_name')
    list_filter = ('latitude',)

    class Media:
        js = ('get_location.js',)  # <- Nombre del archivo que vamos a inyectar

admin.site.register(Client, ClientAdmin)


@admin.register(DebtAccount)
class DebtAccountAdmin(admin.ModelAdmin):
    list_display = ('debtor_name', 'account_number', 'amount_due', 'due_date', 'status', 'hash_id')
    readonly_fields = ('hash_id',)
    search_fields = ('debtor_name', 'account_number')
    list_filter = ('status',)
