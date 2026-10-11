import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.agents.llm import stream_chat
from app.api.deps import get_current_user
from app.db.models import Message, Session, User
from app.db.session import AsyncSessionLocal, get_db

router = APIRouter()

SYSTEM_PROMPT = (
    "你是青问，一位专业、有耐心的 AI 私人教练，擅长健身训练、营养饮食和恢复管理。"
    "回答简洁、务实、可执行。用中文回答。"
)


class ChatRequest(BaseModel):
    message: str
    session_id: int | None = None


@router.post("/chat/stream")
async def chat_stream(
    req: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1) 校验/创建会话
    if req.session_id is not None:
        result = await db.execute(select(Session).where(Session.id == req.session_id))
        sess = result.scalar_one_or_none()
        if sess is None or sess.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        sess = Session(
            user_id=current_user.id,
            thread_id=f"user{current_user.id}-{uuid.uuid4().hex[:12]}",
            title=req.message[:30],
        )
        db.add(sess)
        await db.commit()
        await db.refresh(sess)

    # 2) 加载历史消息
    result = await db.execute(
        select(Message)
        .where(Message.session_id == sess.id)
        .order_by(Message.created_at.asc())
    )
    history = result.scalars().all()

    # 3) 保存用户消息
    db.add(Message(session_id=sess.id, role="user", content=req.message))
    await db.commit()

    # 4) 构造 LLM 消息
    llm_messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in history:
        llm_messages.append({"role": m.role, "content": m.content})
    llm_messages.append({"role": "user", "content": req.message})

    session_id = sess.id
    thread_id = sess.thread_id

    async def event_gen():
        yield {
            "event": "start",
            "data": json.dumps({"session_id": session_id, "thread_id": thread_id}, ensure_ascii=False),
        }

        full = ""
        try:
            async for delta in stream_chat(llm_messages):
                full += delta
                yield {
                    "event": "token",
                    "data": json.dumps({"delta": delta}, ensure_ascii=False),
                }
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"message": f"{type(e).__name__}: {e}"}, ensure_ascii=False),
            }
            return

        # 5) 落库 AI 回复 + 更新会话时间
        async with AsyncSessionLocal() as db2:
            db2.add(
                Message(
                    session_id=session_id,
                    role="assistant",
                    agent="orchestrator",
                    content=full,
                )
            )
            s = (
                await db2.execute(select(Session).where(Session.id == session_id))
            ).scalar_one()
            s.updated_at = datetime.now(timezone.utc)
            await db2.commit()

        yield {
            "event": "end",
            "data": json.dumps({"status": "done", "session_id": session_id}, ensure_ascii=False),
        }

    return EventSourceResponse(event_gen())