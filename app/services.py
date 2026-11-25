import asyncio
import httpx


class WeatherService:
    GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
    OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
    MET_NORWAY_URL = "https://api.met.no/weatherapi/locationforecast/2.0/compact"
    HEADERS = {"User-Agent": "KukoldiniWeather/1.0 github.com/myatavchae"}

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    async def _get_coordinates(
        self, client: httpx.AsyncClient, city: str
    ) -> dict | None:
        params = {"name": city, "count": 1, "language": "ru", "format": "json"}
        res = await client.get(self.GEOCODING_URL, params=params)
        res.raise_for_status()
        data = res.json()
        if "results" in data:
            info = data.get("results")
            if info:
                info = info[0]
                return {
                    "country": info.get("country"),
                    "city": info.get("name"),
                    "lat": info.get("latitude"),
                    "lon": info.get("longitude"),
                }

        return None

    async def _fetch_open_meteo(
        self, client: httpx.AsyncClient, lat: float, lon: float
    ) -> dict:
        res = await client.get(
            self.OPEN_METEO_URL,
            params={
                "latitude": round(lat, 4),
                "longitude": round(lon, 4),
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m",
            },
            headers=self.HEADERS,
        )
        res.raise_for_status()
        data = res.json()
        current = data.get("current", {})
        return {
            "source": "Open-Meteo",
            "temp": current.get("temperature_2m"),
            "humidity": current.get("relative_humidity_2m"),
            "wind_kmh": current.get("wind_speed_10m"),
        }

    async def _fetch_met_norway(
        self, client: httpx.AsyncClient, lat: float, lon: float
    ) -> dict:
        res = await client.get(
            self.MET_NORWAY_URL,
            params={
                "lat": round(lat, 4),
                "lon": round(lon, 4),
            },
            headers=self.HEADERS,
        )
        res.raise_for_status()
        data = res.json()
        details = data["properties"]["timeseries"][0]["data"]["instant"]["details"]
        return {
            "source": "MET Norway",
            "temp": details.get("air_temperature"),
            "humidity": details.get("relative_humidity"),
            "wind_kmh": round(details["wind_speed"] * 3.6, 1),
        }

    async def get_weather(self, city: str) -> dict | None:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            coords = await self._get_coordinates(client, city)

            if coords:
                res_1, res_2 = await asyncio.gather(
                    self._fetch_open_meteo(client, coords["lat"], coords["lon"]),
                    self._fetch_met_norway(client, coords["lat"], coords["lon"]),
                )
                return {
                    "city": f"{coords['city']}, {coords['country']}"
                    if coords.get("country")
                    else coords["city"],
                    "avg_temp": round((res_1["temp"] + res_2["temp"]) / 2, 1),
                    "avg_humidity": round(
                        (res_1["humidity"] + res_2["humidity"]) / 2, 1
                    ),
                    "avg_wind_kmh": round(
                        (res_1["wind_kmh"] + res_2["wind_kmh"]) / 2, 1
                    ),
                    "sources": [res_1, res_2],
                }
            return None


if __name__ == "__main__":
    obj = WeatherService()
    print(asyncio.run(obj.get_weather("Москва")))
