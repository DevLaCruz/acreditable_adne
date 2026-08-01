document.addEventListener('DOMContentLoaded', function () {
    const latitudeField = document.getElementById('id_latitude');
    const longitudeField = document.getElementById('id_longitude');

    if (!latitudeField || !longitudeField) return;

    // Crear botón interactivo para capturar GPS manualmente sin sobreescribir por accidente
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.innerText = '📍 Capturar Mi Ubicación GPS Actual';
    btn.style.cssText = 'margin-top: 8px; display: inline-block; padding: 6px 12px; background: #2563eb; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 600; shadow: 0 1px 2px rgba(0,0,0,0.1);';

    function fetchLocation() {
        if (!navigator.geolocation) {
            alert("La geolocalización no está soportada por tu navegador.");
            return;
        }

        btn.innerText = '⏳ Capturando coordenadas GPS...';
        btn.disabled = true;

        navigator.geolocation.getCurrentPosition(
            function (position) {
                latitudeField.value = position.coords.latitude;
                longitudeField.value = position.coords.longitude;
                btn.innerText = '✅ Coordenadas capturadas';
                btn.style.background = '#059669';
                setTimeout(() => {
                    btn.innerText = '📍 Actualizar Coordenadas GPS';
                    btn.style.background = '#2563eb';
                    btn.disabled = false;
                }, 2500);
            },
            function (error) {
                console.error("Error obteniendo ubicación:", error);
                btn.innerText = '📍 Intentar de nuevo';
                btn.style.background = '#dc2626';
                btn.disabled = false;
            },
            { enableHighAccuracy: true, timeout: 10000 }
        );
    }

    btn.addEventListener('click', fetchLocation);

    // Insertar el botón debajo del campo de longitud
    if (longitudeField.parentNode) {
        longitudeField.parentNode.appendChild(btn);
    }

    // IMPORTANTE: SOLO auto-completar si los campos están VACÍOS (nuevo cliente en campo).
    // Si ya tiene lat/long guardados, NO sobreescribir automáticamente al abrir el detalle.
    const isAlreadySet = latitudeField.value && longitudeField.value && 
                         latitudeField.value.trim() !== '' && longitudeField.value.trim() !== '';

    if (!isAlreadySet) {
        fetchLocation();
    }
});
