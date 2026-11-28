from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, staticfiles, templating, Request

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


@app.get("/")
async def index(request: Request, city: str | None = None):
    weather = None
    error = None
    if city and (city := city.strip()):
        try:
            weather = await weather_service.get_weather(city)
            if weather is not None:
                await weather_database.add_record(
                    weather["city"],
                    weather["avg_temp"],
                    weather["avg_humidity"],
                    weather["avg_wind_kmh"],
                )
            else:
                error = f"Город {city} не найден"

        except httpx.HTTPError:
            error = "Ошибка при обращении к метеосервисам"

    history = await weather_database.get_recent(5)

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "weather": weather,
            "error": error,
            "history": history,
        },
    )


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
