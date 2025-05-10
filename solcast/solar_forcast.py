import requests

from datetime import datetime, timedelta, timezone

API_KEY = 'pcQGd02y83xO6sNrCbvshmvwJRqP4Khd'
RESOURCE_ID = '06f6-7133-3e29-8254'  # Looks like: '1234-abcd-5678-efgh'
LOCAL_TZ = 'America/Los_Angeles'  # Change this to your local timezone
import pytz  # If you don't have it, run: pip install pytz


# Solcast API endpoint
url = f"https://api.solcast.com.au/rooftop_sites/{RESOURCE_ID}/forecasts?format=json&api_key={API_KEY}"

response = requests.get(url)
data = response.json()

# Today's date
today = datetime.now(timezone.utc).date()
#now = datetime.utcnow()
now = datetime.now(timezone.utc)
end_time = now + timedelta(hours=12)
local_time = now.astimezone(pytz.timezone(LOCAL_TZ))

print(f"Forecast for {today}:\n")
for entry in data['forecasts']:
    timestamp = datetime.fromisoformat(entry['period_end'].replace('Z', '+00:00'))
    if timestamp.date() == today:
        print(f"{timestamp.strftime('%H:%M')}: {entry['pv_estimate']} kW")


total_energy_kwh = 0.0
hours_production_remaining = 0

for forecast in data['forecasts']:
    period_end = datetime.fromisoformat(forecast['period_end'].replace('Z', '+00:00'))

    if now <= period_end <= end_time:
        kw = forecast['pv_estimate']
        if kw>.4:
            hours_production_remaining += .5
        interval_minutes = 30  # Solcast usually provides 30-min intervals
        kwh = kw * (interval_minutes / 60.0)
        total_energy_kwh += kwh
        print(f"{period_end.strftime('%H:%M')} - {kw:.2f} kW → {kwh:.2f} kWh")

print(f"\n🔋 Estimated total generation in next 12 hours: {total_energy_kwh:.2f} kWh hrs of production ramaining = {hours_production_remaining:1.1f}")        
print(f"🕒 Current local time: {local_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")