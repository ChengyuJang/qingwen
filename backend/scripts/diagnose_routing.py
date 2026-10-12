"""诊断路由失败：打印 Orchestrator 对这些 query 的实际回答。"""
import asyncio

from agentscope.event import EventType
from agentscope.message import UserMsg

from app.agents.team import build_team

FAILED_QUERIES = [
    "我是新手，175cm 70kg，想减脂，家里有哑铃",
    "昨晚只睡了5小时，今天还能练吗",
    "最近总觉得累，要不要降低训练强度",
    "帮我推荐几个哑铃练胸的动作",
    "我膝盖不好，怎么做深蹲",
    "我想减脂，帮我制定训练和饮食计划",
]


async def diagnose(query: str):
    print(f"\n{'='*70}")
    print(f"Query: {query}")
    print(f"{'-'*70}")

    pipe = await build_team()

    reply_to_agent: dict[str, str] = {}
    orchestrator_text = ""
    delegated = False
    events_log: list[str] = []

    async for evt in pipe.reply_stream(UserMsg(name="user", content=query)):
        if evt.type == EventType.REPLY_START:
            agent = evt.name.lower()
            reply_to_agent[evt.reply_id] = agent
            events_log.append(f"  [REPLY_START] {agent}")

        elif evt.type == EventType.TEXT_BLOCK_DELTA:
            agent = reply_to_agent.get(evt.reply_id, "?")
            if agent == "orchestrator":
                orchestrator_text += evt.delta

        elif evt.type == EventType.TOOL_CALL_START:
            if evt.tool_call_name == "TeamAssign":
                delegated = True
                events_log.append("  [DELEGATE] ✅ 派活了")

        elif evt.type == EventType.REPLY_END:
            agent = reply_to_agent.get(evt.reply_id, "?")
            events_log.append(f"  [REPLY_END] {agent}")

    print("\n事件时间线：")
    for e in events_log[:10]:  # 只看前 10 条
        print(e)
    if len(events_log) > 10:
        print(f"  ... (省略 {len(events_log)-10} 条)")

    print(f"\n是否派活：{'✅ 是' if delegated else '❌ 否'}")
    print(f"\nOrchestrator 回答（完整）：")
    print(f"  {orchestrator_text[:800]}")
    if len(orchestrator_text) > 800:
        print(f"  ... (共 {len(orchestrator_text)} 字)")


async def main():
    for q in FAILED_QUERIES:
        await diagnose(q)


asyncio.run(main())