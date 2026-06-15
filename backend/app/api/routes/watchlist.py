"""
Watchlist routes — manage user's tracked companies.
"""
import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db, get_current_active_user
from app.models.company import Company, UserWatchlist
from app.models.user import User
from app.schemas.company import WatchlistAdd, WatchlistItemRead

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/watchlist", tags=["Watchlist"])


# ---------------------------------------------------------------------------
# GET / — list user's watchlist
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[WatchlistItemRead])
async def get_watchlist(
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[UserWatchlist]:
    """Return all companies on the current user's watchlist."""
    result = await db.execute(
        select(UserWatchlist)
        .options(selectinload(UserWatchlist.company))
        .where(UserWatchlist.user_id == current_user.id)
        .order_by(UserWatchlist.added_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


# ---------------------------------------------------------------------------
# POST / — add a ticker to the watchlist
# ---------------------------------------------------------------------------

@router.post("/", response_model=WatchlistItemRead, status_code=status.HTTP_201_CREATED)
async def add_to_watchlist(
    body: WatchlistAdd,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> UserWatchlist:
    """Add a company to the user's watchlist by ticker symbol."""
    # Resolve company
    result = await db.execute(
        select(Company).where(func.upper(Company.ticker) == body.ticker.upper())
    )
    company = result.scalar_one_or_none()
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with ticker '{body.ticker}' not found",
        )

    # Check for duplicate
    existing = await db.execute(
        select(UserWatchlist).where(
            UserWatchlist.user_id == current_user.id,
            UserWatchlist.company_id == company.id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"'{body.ticker}' is already on your watchlist",
        )

    entry = UserWatchlist(
        user_id=current_user.id,
        company_id=company.id,
        notes=body.notes,
    )
    db.add(entry)
    await db.flush()

    # Reload with relationship for response
    await db.refresh(entry)
    result2 = await db.execute(
        select(UserWatchlist)
        .options(selectinload(UserWatchlist.company))
        .where(UserWatchlist.id == entry.id)
    )
    entry_with_company = result2.scalar_one()

    logger.info("Added to watchlist", ticker=body.ticker, user_id=current_user.id)
    return entry_with_company


# ---------------------------------------------------------------------------
# DELETE /{ticker} — remove from watchlist
# ---------------------------------------------------------------------------

@router.delete("/{ticker}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_watchlist(
    ticker: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """Remove a company from the user's watchlist by ticker symbol."""
    result = await db.execute(
        select(Company).where(func.upper(Company.ticker) == ticker.upper())
    )
    company = result.scalar_one_or_none()
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with ticker '{ticker.upper()}' not found",
        )

    deleted = await db.execute(
        delete(UserWatchlist).where(
            UserWatchlist.user_id == current_user.id,
            UserWatchlist.company_id == company.id,
        )
    )
    if deleted.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"'{ticker.upper()}' is not on your watchlist",
        )

    logger.info("Removed from watchlist", ticker=ticker.upper(), user_id=current_user.id)
