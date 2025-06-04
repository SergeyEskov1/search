from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import Game, Provider
from database import get_db
from typing import Optional
from pydantic import BaseModel


app = FastAPI()

class SearchResult(BaseModel):
    games: list[int] = []
    providers: list[int] = []


@app.get("/search/", response_model=SearchResult)
async def search(
        query: Optional[str] = Query(None, min_length=2, max_length=100),
        db: AsyncSession = Depends(get_db)
):
    result = SearchResult()

    if query:
        # Поиск игр
        games_stmt = select(Game.id).where(Game.title.ilike(f"%{query}%"))
        games_result = await db.execute(games_stmt)
        result.games = [row[0] for row in games_result]

        # Поиск провайдеров
        providers_stmt = select(Provider.id).where(Provider.name.ilike(f"%{query}%"))
        providers_result = await db.execute(providers_stmt)
        result.providers = [row[0] for row in providers_result]

    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)