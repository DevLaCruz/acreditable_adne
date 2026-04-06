document.addEventListener('DOMContentLoaded', function () {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function (position) {
            const latitudeField = document.getElementById('id_latitude');
            const longitudeField = document.getElementById('id_longitude');
            if (latitudeField && longitudeField) {
                latitudeField.value = position.coords.latitude;
                longitudeField.value = position.coords.longitude;
            }
        }, function (error) {
            console.error("Error obteniendo la ubicación:", error);
        });
    } else {
        console.error("La geolocalización no está soportada en este navegador.");
    }
});
