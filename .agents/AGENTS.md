# AGENTS.md - Reglas y Resumen del Proyecto

Este documento registra la arquitectura, decisiones de diseño, convenciones de código y el historial de cambios realizados en la aplicación **Neosuar / Tienda Suárez** (`acreditable_adne`).

---

## 1. Visión General del Sistema y Stack Tecnológico

- **Backend**: Django 5.2 (Python 3.12+)
- **Frontend Interactivo**: HTMX 1.9 + Alpine.js
- **Sistema de Estilos**: Tailwind CSS v3 (Play CDN) + Modo Oscuro automático (`darkMode: 'media'`)
- **Base de Datos**: PostgreSQL en producción (vía Podman/Docker Compose) / SQLite en desarrollo local
- **Contenedores**: Podman / Docker Compose con contenedor `suarez_web`

### Estructura de Aplicaciones

| Aplicación | Descripción |
|---|---|
| `accounts` | Autenticación de usuarios (`Account`), perfiles (`UserProfile`) y dashboard. |
| `store` | Catálogo de productos (`Product`, `Variation`), categorías y reviews. |
| `carts` | Carrito de compras (`Cart`, `CartItem`) interactivo con HTMX. |
| `orders` | Gestión de órdenes y compras (`Order`, `OrderProduct`). |
| `debtscards` | Módulo de cobranzas, tarjetas de crédito/deuda en campo (`Client`, `DebtCard`, `DebtPayment`). |
| `core` | Modelos base abstractos (`CoreModel`) con soporte de Soft Delete y auditoría. |

---

## 2. Convenciones de Estilo y UI (Dark Mode & Inputs)

1. **Color de Fuente e Inputs**:
   - Texto negro de un solo color sobre fondos claros por defecto (`text-slate-900`, `bg-white`, `border-slate-300`).
   - Soporte para Modo Oscuro que responde al tema del usuario (`darkMode: 'media'`).
   - Variantes `dark:` habilitadas para texto claro (`dark:text-slate-100`, `dark:bg-slate-900`, `dark:border-slate-700`).

2. **Estética Visual (Estilo Shadcn-like)**:
   - Bordes redondeados modernos (`rounded-2xl`, `rounded-xl`).
   - Sombras suaves (`shadow-sm`, `shadow-md`).
   - Paleta de colores curated: Slate para neutros e Indigo/Blue para acentos primarios.

---

## 3. Integración de HTMX en el Ecommerce

### Principios de Navegación e Interactividad
- **Sin recargas completas** para agregar/quitar productos, cambiar cantidades, filtrar categorías o paginar.
- Evitar `hx-boost="true"` en la etiqueta `<body>` para impedir conflictos con `hx-target` específicos.

### Flujos y Endpoints HTMX

1. **Catálogo de Tienda (`/store/`)**:
   - Filtros de categorías y paginación utilizan `hx-get` apuntando a `hx-target="#product-list"` con `hx-swap="innerHTML"`.
   - La vista `store` devuelve únicamente el partial `store/partials/product_list.html` cuando recibe `HX-Target: product-list`.

2. **Agregar al Carrito (`add_cart`)**:
   - En la tarjeta del producto: `<button hx-post="{% url 'add_cart' product.id %}" hx-target="#toast-zone" hx-swap="beforeend">`.
   - Devuelve una notificación flotante (Toast) auto-descartable (3s) y dispara el evento `updateCartBadge` para actualizar el contador del navbar.
   - En la vista de producto (`product_detail.html`): El `<form>` usa `hx-post`, `hx-target="#toast-zone"`, `hx-swap="beforeend"`.

3. **Controles de Cantidad en la Página del Carrito (`/cart/`)**:
   - **Incrementar (`+`)**: `<button hx-post="{% url 'add_cart_item' cart_item.product.id cart_item.id %}" hx-target="#cart-content" hx-swap="outerHTML" hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'>`.
     - Incrementa la cantidad del `CartItem` específico según su `id` (independiente de variaciones o de la falta de parámetros POST).
   - **Decrementar (`-`)**: `<button hx-get="{% url 'remove_cart' cart_item.product.id cart_item.id %}" hx-target="#cart-content" hx-swap="outerHTML">`.
     - Reduce la cantidad del `CartItem` específico o lo elimina si llega a 0.
   - **Eliminar Producto**: `<button hx-get="{% url 'remove_cart_item' cart_item.product.id cart_item.id %}" hx-target="#cart-content" hx-swap="outerHTML">`.
   - Todos los endpoints de carrito devuelven `store/partials/cart_content.html` e incluyen la cabecera `HX-Trigger: updateCartBadge`.

4. **Badge del Navbar (`/cart/badge/`)**:
   - El contenedor `#navbar-cart-container` en `navbar_cart.html` escucha el evento `updateCartBadge from:body` para refrescar de forma síncrona el ícono del carrito.

---

## 4. Módulo de Tarjetas de Deuda y Cobranza (`debtscards`)

1. **Diseño de Modelos**:
   - Basado en la tarjeta física de cobranza ("NEGOCIOS SUÁREZ").
   - `DebtCard` registra el monto inicialpretendido a cobrar y mantiene el `balance` (saldo restante `RESTA`).
   - Cada abono se registra como `DebtPayment` y descuenta automáticamente el saldo mediante señales / lógica de guardado.

2. **Geolocalización GPS**:
   - Las coordenadas de latitud y longitud solo se autocompletan en la creación de un cliente nuevo cuando los campos están vacíos.
   - En la vista de detalle del Admin, se requiere hacer clic explícito en el botón de capturar GPS para actualizar coordenadas, evitando la sobreescritura accidental al abrir la ficha.

3. **Auto-asociación de Clientes**:
   - Al registrarse un usuario en la plataforma web (`Account`), el sistema busca coincidencias por número de teléfono en `debtscards.Client` para vincular automáticamente su historial de crédito.

---

## 5. Configuración de Entorno y Despliegue (Podman / Docker)

1. **Variables de Entorno para Base de Datos**:
   - Nombres unificados en `docker-compose.prod.yml` y `settings.py`:
     - `DB_HOST` (valor `db` en contenedor)
     - `DB_NAME`
     - `DB_USER`
     - `DB_PASSWORD`
     - `DB_PORT` (5432)

2. **Comandos Frecuentes**:
   ```bash
   # Reiniciar contenedor en podman
   podman-compose -f docker-compose.prod.yml restart web

   # Ejecutar migraciones en el contenedor
   podman exec -u root suarez_web python manage.py makemigrations
   podman exec -u root suarez_web python manage.py migrate

   # Recopilar archivos estáticos
   podman exec -u root suarez_web python manage.py collectstatic --noinput
   ```
