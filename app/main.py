import httpx
from fastapi import FastAPI, HTTPException

from app.services import WeatherService

app = FastAPI(title="KukoldiniWeather")
weather_service = WeatherService()


@app.get("/api/weather/{city}")
async def get_city_weather(city: str):
    try:
        data = await weather_service.get_weather(city)

    except httpx.HTTPError:
        raise HTTPException(
            status_code=502, detail="Соединение было разорвано(у Норвежцев неполадки)"
        )

    if not data:
        raise HTTPException(status_code=404, detail="Город не найден")

    return data
