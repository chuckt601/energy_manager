import requests

lat, lon = 34.05, -118.25  # Replace with your coordinates
url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m"

response = requests.get(url)
data = response.json()

for time, temp in zip(data['hourly']['time'], data['hourly']['temperature_2m']):
    print(f"{time} → {temp}°C")
 