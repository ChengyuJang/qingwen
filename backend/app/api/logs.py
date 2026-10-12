"""每日追踪打卡接口。"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.models import DailyLog, User
from app.db.session import get_db
from app.schemas import DailyLogCreate, DailyLogOut

router = APIRouter(prefix="/logs", tags=["logs"])


@router.post("", response_model=DailyLogOut, status_code=status.HTTP_201_CREATED)
async def upsert_log(
    req: DailyLogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建/更新某天的打卡。同一天只保留一条。"""
    # 归一化到 UTC 当天 0 点，避免同一天不同时刻存成两条
    day = req.log_date.astimezone(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    result = await db.execute(
        select(DailyLog).where(
            DailyLog.user_id == current_user.id,
            DailyLog.log_date == day,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.trained = req.trained
        existing.training_note = req.training_note
        existing.diet_note = req.diet_note
        existing.sleep_hours = req.sleep_hours
        existing.mood = req.mood
        existing.note = req.note
        await db.commit()
        await db.refresh(existing)
        return existing

    log = DailyLog(
        user_id=current_user.id,
        log_date=day,
        trained=req.trained,
        training_note=req.training_note,
        diet_note=req.diet_note,
        sleep_hours=req.sleep_hours,
        mood=req.mood,
        note=req.note,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


@router.get("", response_model=list[DailyLogOut])
async def list_logs(
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """列出最近 N 天的打卡（默认 30 天）。"""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(DailyLog)
        .where(DailyLog.user_id == current_user.id, DailyLog.log_date >= since)
        .order_by(DailyLog.log_date.desc())
    )
    return result.scalars().all()


@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_log(
    log_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(DailyLog).where(DailyLog.id == log_id))
    log = result.scalar_one_or_none()
    if log is None or log.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Log not found")
    await db.delete(log)
    await db.commit()