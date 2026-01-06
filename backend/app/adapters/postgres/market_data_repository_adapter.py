"""PostgreSQL adapter for market data repository."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, and_, or_, func, case
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.application.ports.market_data_repository import MarketDataRepository
from app.adapters.postgres.models import MarketDataModel, PressingModel, CollectionItemModel


class MarketDataRepositoryAdapter(MarketDataRepository):
    """PostgreSQL implementation of market data repository."""

    def __init__(self, session):
        self._session = session

    async def get_by_pressing_id(self, pressing_id: UUID) -> Optional[dict]:
        """Get market data for a pressing."""
        stmt = select(MarketDataModel).where(MarketDataModel.pressing_id == pressing_id)
        result = await self._session.execute(stmt)
        market_data = result.scalar_one_or_none()

        if not market_data:
            return None

        return {
            "id": market_data.id,
            "pressing_id": market_data.pressing_id,
            "min_value": market_data.min_value,
            "median_value": market_data.median_value,
            "max_value": market_data.max_value,
            "last_sold_price": market_data.last_sold_price,
            "currency": market_data.currency,
            "availability_status": market_data.availability_status,
            "updated_at": market_data.updated_at,
        }

    async def upsert(
        self,
        pressing_id: UUID,
        min_value: float,
        median_value: float,
        max_value: float,
        currency: str,
        last_sold_price: Optional[float] = None,
        availability_status: Optional[str] = None
    ) -> dict:
        """Insert or update market data."""
        stmt = (
            pg_insert(MarketDataModel)
            .values(
                pressing_id=pressing_id,
                min_value=min_value,
                median_value=median_value,
                max_value=max_value,
                currency=currency,
                last_sold_price=last_sold_price,
                availability_status=availability_status,
                updated_at=func.now()
            )
            .on_conflict_do_update(
                index_elements=[MarketDataModel.pressing_id],
                set_={
                    "min_value": min_value,
                    "median_value": median_value,
                    "max_value": max_value,
                    "currency": currency,
                    "last_sold_price": last_sold_price,
                    "availability_status": availability_status,
                    "updated_at": func.now()
                }
            )
            .returning(MarketDataModel)
        )

        result = await self._session.execute(stmt)
        market_data = result.scalar_one()
        await self._session.commit()

        return {
            "id": market_data.id,
            "pressing_id": market_data.pressing_id,
            "min_value": market_data.min_value,
            "median_value": market_data.median_value,
            "max_value": market_data.max_value,
            "currency": market_data.currency,
            "updated_at": market_data.updated_at,
        }

    async def get_stale_pressings(
        self,
        older_than: datetime,
        limit: int = 100
    ) -> List[dict]:
        """Get pressings needing price updates."""
        # Subquery: pressings in collections (prioritize these)
        in_collection_subq = (
            select(CollectionItemModel.pressing_id)
            .distinct()
            .subquery()
        )

        # Left join with market_data to find:
        # 1. Pressings with no market data
        # 2. Pressings with stale market data (older than threshold)
        stmt = (
            select(
                PressingModel.id.label("pressing_id"),
                PressingModel.discogs_release_id,
                MarketDataModel.updated_at,
                case(
                    (PressingModel.id.in_(select(in_collection_subq)), True),
                    else_=False
                ).label("in_collection")
            )
            .outerjoin(MarketDataModel, MarketDataModel.pressing_id == PressingModel.id)
            .where(
                and_(
                    PressingModel.discogs_release_id.isnot(None),  # Must have Discogs ID
                    or_(
                        MarketDataModel.id.is_(None),  # No market data
                        MarketDataModel.updated_at < older_than  # Stale data
                    )
                )
            )
            .order_by(
                case(
                    (PressingModel.id.in_(select(in_collection_subq)), 0),
                    else_=1
                ),  # Prioritize items in collections
                MarketDataModel.updated_at.asc().nullsfirst()  # Oldest first, NULL first
            )
            .limit(limit)
        )

        result = await self._session.execute(stmt)
        rows = result.fetchall()

        return [
            {
                "pressing_id": row.pressing_id,
                "discogs_release_id": row.discogs_release_id,
                "last_updated": row.updated_at,
                "in_collection": row.in_collection,
            }
            for row in rows
        ]

    async def mark_pricing_unavailable(self, pressing_id: UUID) -> None:
        """Mark pricing unavailable to prevent repeated lookups."""
        stmt = (
            pg_insert(MarketDataModel)
            .values(
                pressing_id=pressing_id,
                min_value=None,
                median_value=None,
                max_value=None,
                currency=None,
                updated_at=func.now()
            )
            .on_conflict_do_update(
                index_elements=[MarketDataModel.pressing_id],
                set_={"updated_at": func.now()}
            )
        )
        await self._session.execute(stmt)
        await self._session.commit()
