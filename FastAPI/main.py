from fastapi import FastAPI, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.future import select
import os
from typing import Optional, List
from pydantic import BaseModel
import uuid
import logging
import redis.asyncio as redis
from datetime import timedelta
import json
import asyncio

# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Модели Pydantic
class SearchQuery(BaseModel):
    query: str

class SearchResult(BaseModel):
    games: List[int] = []
    providers: List[int] = []

# Настройка подключения к PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:A89064356126a@db:5432/fastapi_db")
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# Инициализация Redis
redis_client = redis.Redis(host="redis", port=6379, decode_responses=True)

app = FastAPI()

# Dependency для получения асинхронной сессии
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def search_in_database(query: str, db: AsyncSession) -> SearchResult:
    """Выполняет поиск в базе данных"""
    result = SearchResult()
    
    # Поиск игр
    games_result = await db.execute(
        select(Game.id).where(Game.title.ilike(f"%{query}%"))
    )
    result.games = [row[0] for row in games_result]
    
    # Поиск провайдеров (пример, добавьте свою логику)
    providers_result = await db.execute(
        select(Provider.id).where(Provider.name.ilike(f"%{query}%"))
    )
    result.providers = [row[0] for row in providers_result]
    
    return result

@app.post("/search/")
async def search_query(
    query_data: SearchQuery,
    db: AsyncSession = Depends(get_db)
):
    try:
        query = query_data.query
        cache_key = f"search_query:{query}"
        
        # Проверяем кэш
        cached_result = await redis_client.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for key: {cache_key}")
            return {
                'message': 'Search query processed successfully (from cache)',
                'data': json.loads(cached_result),
                'cache': True
            }
        
        logger.info(f"Cache miss for key: {cache_key}")
        
        # Если нет в кэше, запрашиваем из БД
        db_result = await search_in_database(query, db)
        
        # Конвертируем результат в словарь для Redis
        result_dict = db_result.dict()
        
        # Сохраняем в кэш на 1 час
        await redis_client.setex(
            cache_key,
            timedelta(hours=1),
            json.dumps(result_dict)
        )
        
        return {
            'message': 'Search query processed successfully',
            'data': result_dict,
            'cache': False
        }
          
    except Exception as e:
        logger.error(f"Error processing search query: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.get("/")
async def read_root():
    return {"message": "FastAPI + Docker + PostgreSQL + Redis"}

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up...")
    await redis_client.ping()
    logger.info("Connected to Redis")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down...")
    await redis_client.close()
    await engine.dispose()