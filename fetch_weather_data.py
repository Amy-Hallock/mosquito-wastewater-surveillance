"""
fetch_weather_data.py

Fetches historical daily weather data (high/low temperature, rainfall) for
Boston, MA from the Open-Meteo Historical Weather API — used to correlate
with the Normalized Biomass Index (NBI) in Phase 5.

Daily high and low temperatures are used instead of daily mean, since
mosquito development is driven by temperature extremes rather than the
average: overnight lows affect larval survival, and daytime highs affect
metabolic/development rate.

Open-Meteo sources its historical data from national weather services
(including NOAA), is free, and requires no API key.
"""

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


if __name__ == "__main__":
    # Example: Boston weather for the study window (March-October 2026)
    weather = fetch_boston_weather("2026-03-01", "2026-10-31")
    print(weather.head())
    print(f"\nFetched {len(weather)} days of weather data.")

    # Save locally for merging with NBI data in the analysis notebook
    weather.to_csv("boston_weather_2026.csv", index=False)
