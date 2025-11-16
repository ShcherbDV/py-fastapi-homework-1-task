from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.session import get_db
from src.database.models import MovieModel

from src.schemas.movies import MovieDetailResponseSchema, MovieListResponseSchema

router = APIRouter()


@router.get("/movies/{movie_id}/", response_model=MovieDetailResponseSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    return movie


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
    page: int = Query(1, ge=1, description="Page number (must be >= 1)"),
    per_page: int = Query(10, ge=1, le=20, description="Items per page (1–20)"),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(MovieModel).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(stmt)
    movies = result.scalars().all()

    if len(movies) < 1:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_items = await db.scalar(select(func.count()).select_from(MovieModel))

    total_pages = (total_items + per_page - 1) // per_page

    return {
        "movies": movies,
        "prev_page": f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None,
        "next_page": f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None,
        "total_pages": total_pages,
        "total_items": total_items,
    }
