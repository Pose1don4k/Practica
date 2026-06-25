from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import httpx
import asyncio
from datetime import datetime

# Инициализируем приложение FastAPI
app = FastAPI(
    title="OFZ Analytics API",
    description="Микросервис для получения исторических котировок ОФЗ с Московской Биржи",
    version="1.0.0"
)

# Настраиваем CORS, чтобы наш Vue.js компонент
# мог свободно делать запросы к бэкенду с другого порта 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене здесь должны быть внутренние домены компании
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#Модели Pydantic для контракта API
class Candle(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float

class SeriesData(BaseModel):
    year: int
    color: str
    data: List[Candle]

class CandlesResponse(BaseModel):
    primary_series: SeriesData
    secondary_series: SeriesData

# --- Основная логика работы с внешним API ---

async def fetch_moex_data_with_retry(year: int) -> List[dict]:
    """
    Функция делает прямой HTTP-запрос к API Мосбиржи (ISS MOEX).
    В соответствии с ТЗ реализован механизм повторных попыток (retry) - ровно 3 попытки.
    Никакие сторонние библиотеки для Мосбиржи не используются.
    """
    # 24 = интервал 1 день (свеча строится за день)
    # SNDX = группа индексов. RGBI = Индекс гособлигаций РФ 
    url = "https://iss.moex.com/iss/engines/stock/markets/index/boards/SNDX/securities/RGBI/candles.json"
    params = {
        "from": f"{year}-01-01",
        "till": f"{year}-12-31",
        "interval": 24, 
        "start": 0
    }
    
    max_retries = 3
    
    # Используем асинхронный клиент для максимальной скорости
    async with httpx.AsyncClient() as client:
        for attempt in range(1, max_retries + 1):
            try:
                # Делаем запрос. Таймаут 5 секунд
                response = await client.get(url, params=params, timeout=5.0)
                
                # Если биржа ответила 5xx ошибкой, raise_for_status() вызовет исключение, 
                # и мы перейдем в блок except для следующей попытки
                response.raise_for_status() 
                
                data = response.json()
                
                # Структура ответа Мосбиржи специфична, безопасно извлекаем нужные массивы
                candles_data = data.get("candles", {}).get("data", [])
                columns = data.get("candles", {}).get("columns", [])
                
                if not candles_data or not columns:
                    return [] # Если данных за этот год еще нет, возвращаем пустой массив

                # Находим индексы необходимых колонок динамически
                idx_date = columns.index("begin")
                idx_open = columns.index("open")
                idx_close = columns.index("close")
                idx_high = columns.index("high")
                idx_low = columns.index("low")

                formatted_candles = []
                for row in candles_data:
                    # Мосбиржа отдает дату со временем "YYYY-MM-DD HH:MM:SS", отрезаем время
                    date_str = row[idx_date].split(" ")[0] if row[idx_date] else ""
                    formatted_candles.append({
                        "date": date_str,
                        "open": row[idx_open],
                        "high": row[idx_high],
                        "low": row[idx_low],
                        "close": row[idx_close]
                    })
                
                return formatted_candles
                
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                print(f"[Попытка {attempt}/{max_retries}] Ошибка соединения с Мосбиржей: {e}")
                if attempt == max_retries:
                    # Если все 3 попытки исчерпаны, генерируем ошибку 503 для фронтенда
                    raise HTTPException(
                        status_code=503, 
                        detail="Сервис недоступен (ошибка подключения к источнику данных)"
                    )
                # Делаем небольшую паузу перед повторной попыткой
                await asyncio.sleep(0.5)

# --- Эндпоинты ---

@app.get("/api/v1/ofz/candles", response_model=CandlesResponse)
async def get_ofz_candles(year: Optional[int] = Query(None, description="Год для построения графика")):
    """
    Единственный эндпоинт микросервиса.
    Получает свечи за выбранный и предыдущий год. Если год не передан, берет текущий.
    Данные НЕ кэшируются и НЕ сохраняются в БД.
    """
    # 1. Если параметр не передан явно - берем текущий год
    target_year = year if year else datetime.now().year
    previous_year = target_year - 1
    
    # 2. Асинхронно запускаем два запроса к бирже ПАРАЛЛЕЛЬНО!
    # Это гарантирует, что мы получим данные за 2 года почти мгновенно,
    # что позволит с запасом уложиться в нефункциональное требование "< 3 секунд".
    try:
        target_year_data, previous_year_data = await asyncio.gather(
            fetch_moex_data_with_retry(target_year),
            fetch_moex_data_with_retry(previous_year)
        )
    except HTTPException as e:
        # Если биржа упала на ретраях, отдаем 503 статус фронту
        raise e

    # 3. Формируем JSON-ответ строго по формату из нашего Технического Задания
    response_payload = {
        "primary_series": {
            "year": target_year,
            "color": "red",
            "data": target_year_data
        },
        "secondary_series": {
            "year": previous_year,
            "color": "pink",
            "data": previous_year_data
        }
    }
    
    # получили данные и сразу отдали их.
    return response_payload