var UnminedCustomMarkers = {
    isEnabled: false,
    markers: []
};

var LososinskMapData = (function () {
    function resolvePhotoUrl(photo) {
        if (!photo) return 'photos/placeholder-building.svg';
        if (/^(https?:|data:|\/)/i.test(photo)) return photo;
        if (photo.indexOf('photos/') === 0) return photo;
        return 'photos/' + photo;
    }

    function normalizePhotos(item) {
        if (Array.isArray(item.photos) && item.photos.length > 0) {
            return item.photos.map(resolvePhotoUrl);
        }
        if (item.photo) {
            return [resolvePhotoUrl(item.photo)];
        }
        return [resolvePhotoUrl('placeholder-building.svg')];
    }

    function normalizeMarker(item) {
        var photos = normalizePhotos(item);
        return {
            x: Number(item.x),
            z: Number(item.z),
            title: item.title || item.text || 'Объект',
            label: item.label || item.text || item.title || '',
            markerType: item.markerType || 'dot',
            pinColor: item.pinColor || '#d93025',
            dotRadius: item.dotRadius || 6,
            labelMinZoom: Number.isFinite(item.labelMinZoom) ? item.labelMinZoom : 1,
            dotMinZoom: Number.isFinite(item.dotMinZoom) ? item.dotMinZoom : -2,
            description: item.description || '',
            category: item.category || 'Объект',
            address: item.address || '',
            openingHours: item.openingHours || item.hours || '',
            photo: photos[0],
            photos: photos,
        };
    }

    async function load(url) {
        const response = await fetch(url, { cache: 'no-store' });
        if (!response.ok) {
            throw new Error('Не удалось загрузить markers.json');
        }

        const payload = await response.json();
        const markers = Array.isArray(payload.markers) ? payload.markers.map(normalizeMarker) : [];
        UnminedCustomMarkers.isEnabled = true;
        UnminedCustomMarkers.markers = markers;
        return markers;
    }

    return {
        load: load,
        resolvePhotoUrl: resolvePhotoUrl,
    };
})();
