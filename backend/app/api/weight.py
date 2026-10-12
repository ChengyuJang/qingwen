"""体重记录 + 趋势接口。"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.models import User, WeightRecord
from app.db.session import get_db
from app.schemas import WeightCreate, WeightOut, WeightTrendPoint

router = APIRouter(prefix="/weight", tags=["weight"])


@router.post("", response_model=WeightOut, status_code=status.HTTP_201_CREATED)
async def upsert_weight(
    req: WeightCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    day = req.record_date.astimezone(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    result = await db.execute(
        select(WeightRecord).where(
            WeightRecord.user_id == current_user.id,
            WeightRecord.record_date == day,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.weight_kg = req.weight_kg
        existing.note = req.note
        await db.commit()
        await db.refresh(existing)
        return existing

    rec = WeightRecord(
        user_id=current_user.id,
        record_date=day,
        weight_kg=req.weight_kg,
        note=req.note,
    )
    db.add(rec)
    await db.commit()
    await db.refresh(rec)
    return rec


@router.get("", response_model=list[WeightOut])
async def list_weights(
    days: int = 90,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(WeightRecord)
        .where(WeightRecord.user_id == current_user.id, WeightRecord.record_date >= since)
        .order_by(WeightRecord.record_date.asc())
    )
    return result.scalars().all()


@router.get("/trend", response_model=list[WeightTrendPoint])
async def weight_trend(
    days: int = 90,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """给前端画折线图用的精简数据点。"""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(WeightRecord.record_date, WeightRecord.weight_kg)
        .where(WeightRecord.user_id == current_user.id, WeightRecord.record_date >= since)
        .order_by(WeightRecord.record_date.asc())
    )
    return [
        WeightTrendPoint(record_date=row.record_date, weight_kg=row.weight_kg)
        for row in result.all()
    ]


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_weight(
    record_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(WeightRecord).where(WeightRecord.id == record_id))
    rec = result.scalar_one_or_none()
    if rec is None or rec.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Record not found")
    await db.delete(rec)
    await db.commit()