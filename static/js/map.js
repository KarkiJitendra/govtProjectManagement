// This file contains the JavaScript code for initializing the Google Map and adding markers to it.
    function initMap() {
        const map = new google.maps.Map(document.getElementById("map"), {
            zoom: 2,
            center: { lat: 27.826511, lng: 86.215858 },
        });

        const labels = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
        const locations = [
            { lat: -31.56391, lng: 147.154312 },
            { lat: -33.718234, lng: 150.363181 },
            { lat: -34.9285, lng: 138.6007 },
            { lat: -37.8136, lng: 144.9631 },
        ];

        const markers = locations.map((location, i) => {
            return new google.maps.Marker({
                position: location,
                label: labels[i % labels.length],
            });
        });

        const markerCluster = new MarkerClusterer(map, markers, {
            imagePath:
                "https://developers.google.com/maps/documentation/javascript/examples/markerclusterer/m",
        });
    }
