from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, staticfiles, templating

from app.database import DatabaseManager
from app.services import WeatherService

weather_service = WeatherService()
weather_database = DatabaseManager("weather.db")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await weather_database.init_db()
    yield


app = FastAPI(title="KukoldiniWeather", lifespan=lifespan)
app.mount("/static", staticfiles.StaticFiles(directory="app/static"), name="static")
templates = templating.Jinja2Templates(directory="app/templates")


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

    await weather_database.add_record(
        data["city"], data["avg_temp"], data["avg_humidity"], data["avg_wind_kmh"]
    )

    return data


@app.get("/api/history")
async def get_weather_history(limit: int = 5):
    return await weather_database.get_recent(limit)
