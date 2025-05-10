function fetchStatus() {
    fetch("/api/status")
        .then(res => res.json())
        .then(data => {
            document.getElementById("home_battery_charge_rate").innerText = data.home_battery_charge_rate;
            document.getElementById("soc").innerText = data.soc;
        })           
        .catch(err => {
            console.error("Error fetching status:", err);
        });
}

setInterval(fetchStatus, 3000);  // Update every 3 seconds
window.onload = fetchStatus;
