"""
fetch_weather_by_month.py

Fetches historical daily weather data for Boston, MA from the Open-Meteo
Historical Weather API, then splits the results into separate files:

  - One temperature file per month (daily high/low, °F)
  - One rainfall file per month (daily precipitation, in)

This month-by-month breakdown is useful for lining up weather conditions
with the mosquito season (egg hatch through population buildup, roughly
March-July for the early-season window) and for keeping each sampling
month's data easy to inspect on its own.

Open-Meteo sources its historical data from national weather services
(including NOAA), is free, and requires no API key.
"""

import os
import requests
import pandas as pd


def fetch_boston_weather(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetch daily high/low temperature and precipitation for Boston, MA.

    Parameters:
        start_date (str): "YYYY-MM-DD"
        end_date (str): "YYYY-MM-DD"

    Returns:
        pd.DataFrame with columns:
            date, high_temp_f, low_temp_f, rainfall_in
    """
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": 42.3601,       # Boston, MA
        "longitude": -71.0589,
        "start_date": start_date,
        "end_date": end_date,
        "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum"],
        "temperature_unit": "fahrenheit",
        "precipitation_unit": "inch",
        "timezone": "America/New_York",
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    weather_df = pd.DataFrame({
        "date": data["daily"]["time"],
        "high_temp_f": data["daily"]["temperature_2m_max"],
        "low_temp_f": data["daily"]["temperature_2m_min"],
        "rainfall_in": data["daily"]["precipitation_sum"],
    })
    weather_df["date"] = pd.to_datetime(weather_df["date"])

    return weather_df


def split_by_month(weather_df: pd.DataFrame, output_dir: str = "data/weather") -> None:
    """
    Split a weather DataFrame into separate temperature and rainfall CSVs,
    one pair of files per calendar month.

    Output files look like:
        data/weather/2026-03_temperature.csv
        data/weather/2026-03_rainfall.csv
        data/weather/2026-04_temperature.csv
        data/weather/2026-04_rainfall.csv
        ...
    """
    os.makedirs(output_dir, exist_ok=True)

    weather_df["year_month"] = weather_df["date"].dt.strftime("%Y-%m")

    for year_month, group in weather_df.groupby("year_month"):
        temp_df = group[["date", "high_temp_f", "low_temp_f"]]
        rain_df = group[["date", "rainfall_in"]]

        temp_path = os.path.join(output_dir, f"{year_month}_temperature.csv")
        rain_path = os.path.join(output_dir, f"{year_month}_rainfall.csv")

        temp_df.to_csv(temp_path, index=False)
        rain_df.to_csv(rain_path, index=False)

        print(f"Saved {temp_path} ({len(temp_df)} days)")
        print(f"Saved {rain_path} ({len(rain_df)} days)")


if __name__ == "__main__":
    # Early-season window: March (egg hatch/overwintering emergence) through July
    weather = fetch_boston_weather("2026-03-01", "2026-07-31")
    split_by_month(weather, output_dir="data/weather")

    print(f"\nDone. {len(weather)} total days processed into monthly files.")
