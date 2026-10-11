import asyncio
import inspect
import os

from agentscope.agent import Agent
from agentscope.credential import DashScopeCredential
from agentscope.message import UserMsg
from agentscope.model import DashScopeChatModel
from agentscope.pipeline import TeamMember, TeamPipeline
from agentscope.tool import Toolkit


async def main() -> None:
    # ---------- 1. 打印 API 签名 ----------
    print("=" * 60)
    print("TeamPipeline.__init__:")
    print(inspect.signature(TeamPipeline.__init__))
    print()
    print("TeamPipeline public methods:",
          [m for m in dir(TeamPipeline) if not m.startswith("_")])
    print()
    print("TeamMember.__init__:")
    print(inspect.signature(TeamMember.__init__))
    print()

    # ---------- 2. 组装 ----------
    model = DashScopeChatModel(
        credential=DashScopeCredential(api_key=os.getenv("DASHSCOPE_API_KEY")),
        model="qwen-plus",
        stream=True,
    )

    leader = Agent(
        name="Leader",
        system_prompt="你是队长。团队成员：\n- Researcher：调查问题\n把任务分配给合适的成员。",
        model=model,
        toolkit=Toolkit(),
    )

    researcher = Agent(
        name="Researcher",
        system_prompt="你是研究员，回答研究问题。",
        model=model,
        toolkit=Toolkit(),
    )

    pipe = TeamPipeline(
        leader=leader,
        members=[
            TeamMember(agent=researcher, description="调查问题并报告发现。"),
        ],
    )

    # ---------- 3. leader toolkit 是否被自动注入 ----------
    print("=" * 60)
    print("leader toolkit schema (管道组装后)：")
    schemas = await leader.toolkit.get_tool_schemas()
    for s in schemas:
        fn = s.get("function", {})
        print(f"  - {fn.get('name', s)}")

    # ---------- 4. 试跑一次，看事件类型 ----------
    print()
    print("=" * 60)
    print("reply_stream 事件：")
    msg = UserMsg(name="user", content="请帮我调查：什么是 BMI？")
    async for event in pipe.reply_stream(msg):
        print(f"  [event] {event.type}", flush=True)


asyncio.run(main())