import asyncio

from agentscope.event import EventType
from agentscope.message import UserMsg

from app.agents.team import build_team


async def ask(pipe, question: str):
    print(f"\n{'='*70}")
    print(f"用户：{question}")
    print(f"{'-'*70}")

    msg = UserMsg(name="user", content=question)
    async for event in pipe.reply_stream(msg):
        # 只显示关键事件，避免刷屏
        if event.type == EventType.TEXT_BLOCK_DELTA:
            print(event.delta, end="", flush=True)
        elif event.type == EventType.TOOL_CALL_START:
            print(f"\n>>> [Orchestrator 派活: {event.tool_call_name}]", flush=True)
    print()


async def main():
    pipe = await build_team()

    # 测试 1：简单招呼，不该派活
    await ask(pipe, "你好")

    # 测试 2：模糊需求，应该先派 Intake
    await ask(pipe, "我想开始健身")

    # 测试 3：明确需求，可能派 Training
    await ask(pipe, "我 70kg，175cm，30岁男，有哑铃，想练腿，给我排个训练")


asyncio.run(main())