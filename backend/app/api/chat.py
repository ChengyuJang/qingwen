import json
import uuid
from app.agents.observability import RequestTrace
import structlog
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db.models import Message, Plan, Session, User

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.api.deps import get_current_user
from app.db.models import Message, Session, User
from app.db.session import AsyncSessionLocal, get_db

logger = structlog.get_logger("chat")
router = APIRouter()

_AGENT_NAME_MAP = {
    "Orchestrator": "orchestrator",
    "Intake": "intake",
    "Training": "training",
    "Nutrition": "nutrition",
    "Recovery": "recovery",
}


def _norm(name: str) -> str:
    return _AGENT_NAME_MAP.get(name, name.lower())


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

    # 2) 落库用户消息
    db.add(Message(session_id=sess.id, role="user", content=req.message))
    await db.commit()

    session_id = sess.id
    thread_id = sess.thread_id
    user_message = req.message

    async def event_gen():
        print("\n[SSE] 1. event_gen 开始", flush=True)
        yield {
            "event": "start",
            "data": json.dumps(
                {"session_id": session_id, "thread_id": thread_id},
                ensure_ascii=False,
            ),
        }
        print("[SSE] 2. start 已发送", flush=True)

        try:
            print("[SSE] 3. 开始 import", flush=True)
            trace = RequestTrace(request_id=thread_id)
            from agentscope.event import EventType
            from agentscope.message import UserMsg
            from app.agents.team import build_team
            print("[SSE] 4. import 完成", flush=True)

            print("[SSE] 5. 开始 build_team", flush=True)
            pipe = await build_team()
            print("[SSE] 6. build_team 完成", flush=True)

            reply_to_agent: dict[str, str] = {}
            agent_buffers: dict[str, str] = {}

            user_msg = UserMsg(name="user", content=user_message)
            print("[SSE] 7. 开始 reply_stream", flush=True)

            async for evt in pipe.reply_stream(user_msg):
                etype = evt.type
                agent = reply_to_agent.get(getattr(evt, "reply_id", ""), "unknown")

                if etype == EventType.REPLY_START:
                    agent = _norm(evt.name)
                    reply_to_agent[evt.reply_id] = agent
                    agent_buffers.setdefault(agent, "")
                    trace.on_reply_start(evt.reply_id, agent)
                    yield {
                        "event": "agent_start",
                        "data": json.dumps({"agent": agent}, ensure_ascii=False),
                    }

                elif etype == EventType.MODEL_CALL_START:
                    trace.on_model_call_start(evt.reply_id, agent)

                elif etype == EventType.MODEL_CALL_END:
                    trace.on_model_call_end(
                        evt.reply_id,
                        getattr(evt, "input_tokens", 0),
                        getattr(evt, "output_tokens", 0),
                        getattr(evt, "finished_reason", ""),
                    )

                elif etype == EventType.TEXT_BLOCK_DELTA:
                    agent_buffers[agent] = agent_buffers.get(agent, "") + evt.delta
                    yield {
                        "event": "token",
                        "data": json.dumps(
                            {"delta": evt.delta, "agent": agent},
                            ensure_ascii=False,
                        ),
                    }

                elif etype == EventType.TOOL_CALL_START:
                    trace.on_tool_call_start(evt.tool_call_id, agent, evt.tool_call_name)
                    if evt.tool_call_name == "TeamAssign":
                        yield {
                            "event": "delegate",
                            "data": json.dumps({"from": agent}, ensure_ascii=False),
                        }
                    else:
                        yield {
                            "event": "tool_call",
                            "data": json.dumps(
                                {"agent": agent, "tool": evt.tool_call_name},
                                ensure_ascii=False,
                            ),
                        }

                elif etype == EventType.TOOL_RESULT_END:
                    trace.on_tool_result_end(
                        evt.tool_call_id,
                        getattr(evt, "state", "unknown"),
                    )

                elif etype == EventType.REPLY_END:
                    yield {
                        "event": "agent_end",
                        "data": json.dumps({"agent": agent}, ensure_ascii=False),
                    }

            # 流结束，输出 trace
            trace.emit()

        except Exception as e:
            import traceback
            print("\n" + "=" * 60, flush=True)
            print(f"[SSE] 异常：{type(e).__name__}: {e}", flush=True)
            traceback.print_exc()
            print("=" * 60 + "\n", flush=True)
            yield {
                "event": "error",
                "data": json.dumps(
                    {"message": f"{type(e).__name__}: {e}"},
                    ensure_ascii=False,
                ),
            }
            return

        # 落库
        async with AsyncSessionLocal() as db2:
            # 1) Orchestrator 汇总 → messages 表
            final = agent_buffers.get("orchestrator", "")
            if final.strip():
                db2.add(
                    Message(
                        session_id=session_id,
                        role="assistant",
                        agent="orchestrator",
                        content=final,
                    )
                )

            # 2) 各专家输出 → plans 表（upsert：同 session + kind 只保留最新）
            PLAN_KINDS = {"training", "nutrition", "recovery"}
            for agent_name, content in agent_buffers.items():
                if agent_name not in PLAN_KINDS:
                    continue
                if not content.strip():
                    continue
                summary = content[:120].replace("\n", " ")
                stmt = (
                    pg_insert(Plan)
                    .values(
                        session_id=session_id,
                        user_id=current_user.id,
                        kind=agent_name,
                        content={"text": content},
                        summary=summary,
                    )
                    .on_conflict_do_update(
                        constraint="uq_plan_session_kind",
                        set_={
                            "content": {"text": content},
                            "summary": summary,
                        },
                    )
                )
                await db2.execute(stmt)

            # 3) 更新会话时间
            s = (
                await db2.execute(select(Session).where(Session.id == session_id))
            ).scalar_one()
            s.updated_at = datetime.now(timezone.utc)
            await db2.commit()

        yield {
            "event": "end",
            "data": json.dumps(
                {"status": "done", "session_id": session_id},
                ensure_ascii=False,
            ),
        }
    return EventSourceResponse(event_gen())