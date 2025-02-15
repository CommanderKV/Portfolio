
if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(accepted, denied);
}

function accepted(position) {
    const latitude = position.coords.latitude;
    const longitude = position.coords.longitude;

    fetch('/geo', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({latitude, longitude})
    })
}

function denied() {
    console.log('Location denied');
}