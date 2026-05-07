import os
import sys
import requests
import time
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("WEATHER_API_KEY")

api_url = "https://api.weatherapi.com/v1/forecast.json"

zip_codes = [
    "90045",  # Los Angeles, CA
    "10001",  # New York, NY
    "60601",  # Chicago, IL
    "98101",  # Seattle, WA
    "33101",  # Miami, FL
    "77001",  # Houston, TX
    "85001",  # Phoenix, AZ
    "19101",  # Philadelphia, PA
    "78201",  # San Antonio, TX
    "92101",  # San Diego, CA
    "75201",  # Dallas, TX
    "95101",  # San Jose, CA
    "78701",  # Austin, TX
    "32201",  # Jacksonville, FL
    "43201",  # Columbus, OH
    "28201",  # Charlotte, NC
    "46201",  # Indianapolis, IN
    "94102",  # San Francisco, CA
    "80201",  # Denver, CO
    "02101",  # Boston, MA
]

results = []

for zip_code in zip_codes:
    params = {
        "key": api_key,
        "q": zip_code,
        "days": 7,
    }
    response = requests.get(api_url, params=params)
    if response.status_code != 200:
        print(f"API error for {zip_code} (HTTP {response.status_code}): {response.text}")
        sys.exit(1)
    data = response.json()

    city = data["location"]["name"]
    region = data["location"]["region"]

    for day in data["forecast"]["forecastday"]:
        record = {
            "zip_code": zip_code,
            "city": city,
            "region": region,
            "date": day["date"],
            "max_temp_f": day["day"]["maxtemp_f"],
            "min_temp_f": day["day"]["mintemp_f"],
            "condition": day["day"]["condition"]["text"],
        }
        results.append(record)
        print(f"{city}, {region} | {record['date']}: {record['min_temp_f']}–{record['max_temp_f']}°F, {record['condition']}")

    time.sleep(1)

print(f"\nCollected {len(results)} forecast records across {len(zip_codes)} cities.")

df = pd.DataFrame(results)
print(df.to_string(index=False))
print(f"\nShape: {df.shape[0]} rows x {df.shape[1]} columns")

df.to_csv("weather_data.csv", index=False)
print("Saved to weather_data.csv")