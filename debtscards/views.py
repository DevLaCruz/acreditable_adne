from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.utils import timezone
from .models import Client, DebtCard, DebtPayment
from accounts.models import Account


def is_staff_or_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_admin or user.is_superadmin)


@login_required(login_url='login')
@user_passes_test(is_staff_or_admin)
def client_list(request):
    """
    Vista principal de Administración de Clientes y Cobranzas:
    Lista de clientes, filtro por sector, buscador en vivo, mapa interactivo.
    """
    query = request.GET.get('q', '').strip()
    sector_filter = request.GET.get('sector', '').strip()

    clients = Client.objects.all().prefetch_related('debt_cards')

    if query:
        clients = clients.filter(
            Q(know_name__icontains=query) |
            Q(phone_number__icontains=query) |
            Q(address__icontains=query) |
            Q(user__email__icontains=query)
        )

    if sector_filter:
        clients = clients.filter(sector__iexact=sector_filter)

    # Obtener lista de sectores únicos para el filtro
    sectors = Client.objects.exclude(sector='').values_list('sector', flat=True).distinct()

    # Preparar datos de geolocalización para el mapa interactivo JS
    map_clients = []
    total_active_cards = 0
    total_system_balance = 0

    for client in clients:
        balance = client.total_balance
        total_system_balance += balance
        total_active_cards += client.active_cards_count

        if client.latitude and client.longitude:
            map_clients.append({
                'id': client.id,
                'name': client.know_name or (client.user.full_name() if client.user else "Cliente"),
                'address': client.address,
                'sector': client.sector,
                'lat': client.latitude,
                'lng': client.longitude,
                'balance': float(balance),
                'cards': client.active_cards_count,
            })

    context = {
        'clients': clients,
        'query': query,
        'sector_filter': sector_filter,
        'sectors': sectors,
        'map_clients_json': map_clients,
        'total_clients': clients.count(),
        'total_active_cards': total_active_cards,
        'total_system_balance': total_system_balance,
    }
    return render(request, 'debtscards/client_list.html', context)


@login_required(login_url='login')
@user_passes_test(is_staff_or_admin)
def client_detail(request, client_id):
    """
    Detalle de un Cliente: Sus fichas/tarjetas activas y cerradas, su mapa de ubicación.
    """
    client = get_object_or_404(Client, id=client_id)
    cards = client.debt_cards.all()

    context = {
        'client': client,
        'cards': cards,
        'active_cards': cards.filter(status='active'),
        'closed_cards': cards.exclude(status='active'),
    }
    return render(request, 'debtscards/client_detail.html', context)


@login_required(login_url='login')
@user_passes_test(is_staff_or_admin)
def client_create(request):
    """
    Crear un nuevo Cliente desde el Dashboard Admin con captura de mapa.
    """
    if request.method == 'POST':
        know_name = request.POST.get('know_name', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        address = request.POST.get('address', '').strip()
        sector = request.POST.get('sector', '').strip()
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')

        if not know_name:
            messages.error(request, "El nombre del cliente es obligatorio.")
            return render(request, 'debtscards/client_form.html')

        client = Client.objects.create(
            know_name=know_name,
            phone_number=phone_number,
            address=address,
            sector=sector,
            latitude=float(latitude) if latitude else None,
            longitude=float(longitude) if longitude else None,
        )

        messages.success(request, f"Cliente {client.know_name} creado exitosamente.")
        return redirect('client_detail', client_id=client.id)

    return render(request, 'debtscards/client_form.html')


@login_required(login_url='login')
@user_passes_test(is_staff_or_admin)
def card_detail(request, card_id):
    """
    Réplica digital de la Tarjeta Azul física:
    Muestra la Ficha Nº, Artículo, Pacto (S/Q/M), y la tabla de abonos (FECHA | PAGO | RESTA).
    """
    card = get_object_or_404(DebtCard, id=card_id)
    payments = card.payments.all()
    collectors = Account.objects.filter(Q(is_staff=True) | Q(is_admin=True))

    context = {
        'card': card,
        'payments': payments,
        'collectors': collectors,
        'today': timezone.now().date(),
    }
    return render(request, 'debtscards/card_detail.html', context)


@login_required(login_url='login')
@user_passes_test(is_staff_or_admin)
def card_create(request, client_id):
    """
    Crear una nueva Tarjeta de Deuda para un cliente.
    """
    client = get_object_or_404(Client, id=client_id)

    if request.method == 'POST':
        card_number = request.POST.get('card_number', '').strip()
        article_description = request.POST.get('article_description', '').strip()
        total_amount = request.POST.get('total_amount', '0')
        payment_frequency = request.POST.get('payment_frequency', 'S')
        agreed_quota = request.POST.get('agreed_quota', '0')
        start_date = request.POST.get('start_date') or timezone.now().date()
        collector_id = request.POST.get('collector_id')

        try:
            total_val = float(total_amount)
            quota_val = float(agreed_quota)

            collector = Account.objects.filter(id=collector_id).first() if collector_id else request.user

            card = DebtCard.objects.create(
                card_number=card_number,
                client=client,
                article_description=article_description,
                total_amount=total_val,
                balance=total_val,
                payment_frequency=payment_frequency,
                agreed_quota=quota_val,
                start_date=start_date,
                collector=collector,
            )

            messages.success(request, f"Tarjeta #{card.card_number} creada exitosamente.")
            return redirect('card_detail', card_id=card.id)
        except Exception as e:
            messages.error(request, f"Error creando la tarjeta: {str(e)}")

    context = {
        'client': client,
        'collectors': Account.objects.filter(Q(is_staff=True) | Q(is_admin=True)),
        'today': timezone.now().date(),
    }
    return render(request, 'debtscards/card_form.html', context)


@login_required(login_url='login')
@user_passes_test(is_staff_or_admin)
def payment_add(request, card_id):
    """
    Registrar un abono/pago en la Tarjeta.
    """
    card = get_object_or_404(DebtCard, id=card_id)

    if request.method == 'POST':
        payment_date = request.POST.get('payment_date') or timezone.now().date()
        amount = request.POST.get('amount', '0')
        collector_id = request.POST.get('collector_id')
        notes = request.POST.get('notes', '').strip()

        try:
            amount_val = float(amount)
            collector = Account.objects.filter(id=collector_id).first() if collector_id else request.user

            payment = DebtPayment.objects.create(
                card=card,
                payment_date=payment_date,
                amount=amount_val,
                collector=collector,
                notes=notes,
            )

            messages.success(request, f"Abono de S/ {amount_val:.2f} registrado correctamente.")
        except Exception as e:
            messages.error(request, f"Error registrando el abono: {str(e)}")

    return redirect('card_detail', card_id=card.id)
