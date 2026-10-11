import asyncio

from agentscope.event import EventType
from agentscope.message import UserMsg

from app.agents.specialists import build_specialist


async def ask(name: str, question: str):
    print(f"\n{'='*60}")
    print(f"[{name}] 问：{question}")
    print(f"{'-'*60}")

    agent = await build_specialist(name)

    # 调试：确认 toolkit 真的注册了工具（get_tool_schemas 也是 async）
    print(f"[debug] toolkit type: {type(agent.toolkit).__name__}")
    try:
        schemas = await agent.toolkit.get_tool_schemas()
        print(f"[debug] 已注册 {len(schemas)} 个工具：")
        for s in schemas:
            print(f"    - {s.get('name', s)}")
    except Exception as e:
        print(f"[debug] 拿 schema 失败: {type(e).__name__}: {e}")

    msg = UserMsg(name="user", content=question)

    async for event in agent.reply_stream(msg):
        # 打印所有事件类型
        print(f"\n[event] type={event.type}", flush=True)

        # 打印 event 对象的所有属性
        if hasattr(event, "__dict__"):
            for k, v in vars(event).items():
                if k.startswith("_"):
                    continue
                print(f"    {k} = {v!r}", flush=True)

        if event.type == EventType.TEXT_BLOCK_DELTA:
            print(event.delta, end="", flush=True)
    print()


async def main():
    await ask("training", "我 70kg，175cm，30岁，男，每周练3次，帮我算一下 BMI 和 TDEE")


asyncio.run(main())