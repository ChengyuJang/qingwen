import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.models import Message, Session, User
from app.db.session import get_db
from app.schemas import MessageOut, SessionCreate, SessionOut

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
async def create_session(
    req: SessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建新会话。thread_id 由后端生成，前端只关心 title。"""
    sess = Session(
        user_id=current_user.id,
        thread_id=f"user{current_user.id}-{uuid.uuid4().hex[:12]}",
        title=req.title,
    )
    db.add(sess)
    await db.commit()
    await db.refresh(sess)
    return sess


@router.get("", response_model=list[SessionOut])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """列出当前用户的所有会话，按更新时间倒序。"""
    result = await db.execute(
        select(Session)
        .where(Session.user_id == current_user.id)
        .order_by(Session.updated_at.desc())
    )
    return result.scalars().all()


@router.get("/{session_id}", response_model=SessionOut)
async def get_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sess = await _get_owned_session(session_id, current_user.id, db)
    return sess


@router.get("/{session_id}/messages", response_model=list[MessageOut])
async def list_messages(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """读取某会话的全部消息（时间正序）。"""
    await _get_owned_session(session_id, current_user.id, db)
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
    )
    return result.scalars().all()


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sess = await _get_owned_session(session_id, current_user.id, db)
    await db.delete(sess)
    await db.commit()


# ---------- helper ----------
async def _get_owned_session(
    session_id: int, user_id: int, db: AsyncSession
) -> Session:
    """取会话并校验归属，防止越权访问别人的会话。"""
    result = await db.execute(select(Session).where(Session.id == session_id))
    sess = result.scalar_one_or_none()
    if sess is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if sess.user_id != user_id:
        # 故意返回 404 而不是 403，避免泄露"该 id 存在但不属于你"
        raise HTTPException(status_code=404, detail="Session not found")
    return sess