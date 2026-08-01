from django.contrib import admin
from .models import Client, DebtCard, DebtPayment, DebtAccount


class DebtPaymentInline(admin.TabularInline):
    model = DebtPayment
    extra = 1
    fields = ('payment_date', 'amount', 'balance_after', 'collector', 'notes')
    readonly_fields = ('balance_after',)


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('know_name', 'user', 'phone_number', 'sector', 'latitude', 'longitude', 'view_on_map')
    readonly_fields = ('hash_id', 'view_on_map')
    search_fields = ('know_name', 'phone_number', 'sector', 'user__email', 'user__first_name', 'user__last_name')
    list_filter = ('sector',)

    class Media:
        js = ('get_location.js',)


@admin.register(DebtCard)
class DebtCardAdmin(admin.ModelAdmin):
    list_display = ('card_number', 'client', 'article_description', 'total_amount', 'balance', 'payment_frequency', 'agreed_quota', 'status', 'collector', 'start_date')
    readonly_fields = ('hash_id',)
    search_fields = ('card_number', 'client__know_name', 'article_description')
    list_filter = ('status', 'payment_frequency', 'start_date', 'collector')
    inlines = [DebtPaymentInline]


@admin.register(DebtPayment)
class DebtPaymentAdmin(admin.ModelAdmin):
    list_display = ('card', 'payment_date', 'amount', 'balance_after', 'collector', 'notes')
    search_fields = ('card__card_number', 'card__client__know_name', 'notes')
    list_filter = ('payment_date', 'collector')


@admin.register(DebtAccount)
class DebtAccountAdmin(admin.ModelAdmin):
    list_display = ('debtor_name', 'account_number', 'amount_due', 'due_date', 'status', 'hash_id')
    readonly_fields = ('hash_id',)
    search_fields = ('debtor_name', 'account_number')
    list_filter = ('status',)
