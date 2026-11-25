import aiosqlite


class DatabaseManager:
    def __init__(self, name: str = "weather.db"):
        self.db_name = name

    async def init_db(self):
        pattern = """
        CREATE TABLE IF NOT EXISTS weather (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city TEXT NOT NULL,
        avg_temp REAL NOT NULL,
        avg_humidity REAL NOT NULL,
        avg_wind_kmh REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        async with aiosqlite.connect(self.db_name) as db:
            async with db.cursor() as cur:
                await cur.execute(pattern)

            await db.commit()

    async def add_record(self, city, avg_temp, avg_humidity, avg_wind_kmh):
        pattern = """
        INSERT INTO weather (city, avg_temp, avg_humidity, avg_wind_kmh) 
        VALUES (?, ?, ?, ?)
        """
        async with aiosqlite.connect(self.db_name) as db:
            async with db.cursor() as cur:
                await cur.execute(pattern, (city, avg_temp, avg_humidity, avg_wind_kmh))

            await db.commit()

    async def get_recent(self, limit) -> list[dict]:
        pattern = """
        SELECT MAX(id) AS last_id, city, avg_temp, avg_humidity, avg_wind_kmh, MAX(created_at) FROM weather
        GROUP BY city
        ORDER BY MAX(id) DESC LIMIT ?
        """
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.cursor() as cur:
                await cur.execute(pattern, (limit,))
                res = await cur.fetchall()

        return [dict(i) for i in res]
