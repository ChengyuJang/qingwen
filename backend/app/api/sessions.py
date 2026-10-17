import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.models import Message, Session, User
from app.db.session import get_db
from app.schemas import MessageOut, SessionCreate, SessionOut, SessionWithPreview

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


@router.get("", response_model=list[SessionWithPreview])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """列出当前用户的所有会话，带最后一条消息预览。"""
    result = await db.execute(
        select(Session)
        .where(Session.user_id == current_user.id)
        .order_by(Session.updated_at.desc())
    )
    sessions = result.scalars().all()
    if not sessions:
        return []

    session_ids = [s.id for s in sessions]

    # 一次性查所有会话的最后一条消息
    latest_subq = (
        select(Message.session_id, Message.content, Message.created_at)
        .where(Message.session_id.in_(session_ids))
        .order_by(Message.session_id, Message.created_at.desc())
        .distinct(Message.session_id)
    )
    msg_result = await db.execute(latest_subq)
    preview_map = {}
    for row in msg_result.all():
        preview = row.content[:60] if row.content else ""
        preview_map[row.session_id] = preview + ("..." if row.content and len(row.content) > 60 else "")

    return [
        SessionWithPreview(
            id=s.id,
            thread_id=s.thread_id,
            title=s.title,
            created_at=s.created_at,
            updated_at=s.updated_at,
            last_message=preview_map.get(s.id),
        )
        for s in sessions
    ]


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