"""报告接口。"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.report import generate_report
from app.api.deps import get_current_user
from app.db.models import Report, User
from app.db.session import get_db
from app.schemas import ReportGenerateRequest, ReportOut

router = APIRouter(prefix="/reports", tags=["reports"])

DEFAULT_DAYS = {"weekly": 7, "monthly": 30}


@router.post("/generate", response_model=ReportOut, status_code=status.HTTP_201_CREATED)
async def generate(
    req: ReportGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """生成一份新报告（会落库）。"""
    if req.kind not in DEFAULT_DAYS:
        raise HTTPException(status_code=400, detail="kind must be weekly or monthly")

    days = req.days if req.days is not None else DEFAULT_DAYS[req.kind]
    days = max(1, min(days, 365))

    report = await generate_report(current_user.id, days=days, kind=req.kind)
    return report


@router.get("", response_model=list[ReportOut])
async def list_reports(
    kind: str | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """列出当前用户的报告（按时间倒序）。"""
    stmt = select(Report).where(Report.user_id == current_user.id)
    if kind:
        stmt = stmt.where(Report.kind == kind)
    stmt = stmt.order_by(Report.created_at.desc()).limit(min(limit, 200))
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{report_id}", response_model=ReportOut)
async def get_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if report is None or report.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.delete("/{report_id}", status_code=204)
async def delete_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if report is None or report.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Report not found")
    await db.delete(report)
    await db.commit()