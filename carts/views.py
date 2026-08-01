from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from store.models import Product, Variation
from .models import Cart, CartItem
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required


def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart


def _get_cart_data(request):
    """Helper para obtener los ítems y la cantidad total del carrito."""
    quantity = 0
    cart_items = []
    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True).select_related('product')
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True).select_related('product')

        for cart_item in cart_items:
            quantity += cart_item.quantity
    except ObjectDoesNotExist:
        pass
    return cart_items, quantity


def cart_badge(request):
    """Componente parcial de HTMX para refrescar el ícono del carrito en el Navbar."""
    cart_items, quantity = _get_cart_data(request)
    context = {
        'cart_count': quantity,
        'cart_items': cart_items,
    }
    return render(request, 'includes/navbar_cart.html', context)


def add_cart(request, product_id, cart_item_id=None):
    product = Product.objects.get(id=product_id)
    current_user = request.user
    product_variation = []

    if cart_item_id:
        try:
            if current_user.is_authenticated:
                cart_item = CartItem.objects.get(product=product, user=current_user, id=cart_item_id)
            else:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
            cart_item.quantity += 1
            cart_item.save()
        except CartItem.DoesNotExist:
            pass
    else:
        if request.method == "POST":
            for item in request.POST:
                key = item
                value = request.POST[key]
                try:
                    variation = Variation.objects.get(
                        product=product,
                        variation_category__iexact=key,
                        variation_value__iexact=value,
                    )
                    product_variation.append(variation)
                except:
                    pass

        if current_user.is_authenticated:
            cart_items_qs = CartItem.objects.filter(product=product, user=current_user)
            if cart_items_qs.exists():
                ex_var_list = [list(item.variations.all()) for item in cart_items_qs]
                id_list = [item.id for item in cart_items_qs]

                if product_variation in ex_var_list:
                    index = ex_var_list.index(product_variation)
                    item = CartItem.objects.get(product=product, id=id_list[index])
                    item.quantity += 1
                    item.save()
                else:
                    item = CartItem.objects.create(product=product, quantity=1, user=current_user)
                    if len(product_variation) > 0:
                        item.variations.clear()
                        item.variations.add(*product_variation)
                    item.save()
            else:
                item = CartItem.objects.create(product=product, quantity=1, user=current_user)
                if len(product_variation) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variation)
                item.save()
        else:
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
            except Cart.DoesNotExist:
                cart = Cart.objects.create(cart_id=_cart_id(request))
            cart.save()

            cart_items_qs = CartItem.objects.filter(product=product, cart=cart)
            if cart_items_qs.exists():
                ex_var_list = [list(item.variations.all()) for item in cart_items_qs]
                id_list = [item.id for item in cart_items_qs]

                if product_variation in ex_var_list:
                    index = ex_var_list.index(product_variation)
                    item = CartItem.objects.get(product=product, id=id_list[index])
                    item.quantity += 1
                    item.save()
                else:
                    item = CartItem.objects.create(product=product, quantity=1, cart=cart)
                    if len(product_variation) > 0:
                        item.variations.clear()
                        item.variations.add(*product_variation)
                    item.save()
            else:
                item = CartItem.objects.create(product=product, quantity=1, cart=cart)
                if len(product_variation) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variation)
                item.save()

    # ── Respuesta HTMX ──────────────────────────────────────────────────────
    if request.headers.get("HX-Request"):
        hx_target = request.headers.get("HX-Target", "")
        cart_items, quantity = _get_cart_data(request)

        # Viene del botón + en la página del carrito → refresca el contenido del carrito
        if hx_target == "cart-content":
            context = {'cart_items': cart_items, 'quantity': quantity}
            response = render(request, 'store/partials/cart_content.html', context)
            response['HX-Trigger'] = 'updateCartBadge'
            return response

        # Viene del botón en tarjeta de producto (toast-zone) → toast con auto-remove
        toast_html = (
            f'<div id="toast-{product.id}" '
            f'class="pointer-events-auto bg-slate-900 text-white dark:bg-white dark:text-slate-900 '
            f'px-5 py-3.5 rounded-2xl shadow-2xl flex items-center gap-3 text-sm font-semibold '
            f'border border-slate-700 dark:border-slate-200 animate-bounce" '
            f'style="animation-iteration-count:2;">'
            f'<span>🛒</span> "{product.product_name}" agregado al carrito'
            f'</div>'
            f'<script>setTimeout(()=>document.getElementById("toast-{product.id}")?.remove(),3000);</script>'
        )
        response = HttpResponse(toast_html)
        response['HX-Trigger'] = 'updateCartBadge'
        return response

    return redirect("cart")


def remove_cart(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)

        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except:
        pass

    if request.headers.get("HX-Request"):
        cart_items, quantity = _get_cart_data(request)
        context = {'cart_items': cart_items, 'quantity': quantity}
        response = render(request, 'store/partials/cart_content.html', context)
        response['HX-Trigger'] = 'updateCartBadge'
        return response

    return redirect("cart")


def remove_cart_item(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
        cart_item.delete()
    except:
        pass

    if request.headers.get("HX-Request"):
        cart_items, quantity = _get_cart_data(request)
        context = {'cart_items': cart_items, 'quantity': quantity}
        response = render(request, 'store/partials/cart_content.html', context)
        response['HX-Trigger'] = 'updateCartBadge'
        return response

    return redirect("cart")


def cart(request):
    cart_items, quantity = _get_cart_data(request)
    context = {
        "quantity": quantity,
        "cart_items": cart_items,
    }
    if request.headers.get("HX-Request") and request.headers.get("HX-Target") == "cart-content":
        return render(request, "store/partials/cart_content.html", context)

    return render(request, "store/cart.html", context)


@login_required(login_url="login")
def checkout(request):
    cart_items, quantity = _get_cart_data(request)
    context = {
        "quantity": quantity,
        "cart_items": cart_items,
    }
    return render(request, "store/checkout.html", context)
