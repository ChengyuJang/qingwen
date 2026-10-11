"""4 个专家 Agent 的实例化。"""
from agentscope.agent import Agent

from app.agents.model import get_model
from app.agents.prompts import get_prompt
from app.agents.tools import (
    build_intake_toolkit,
    build_nutrition_toolkit,
    build_recovery_toolkit,
    build_training_toolkit,
)

_SPECIALISTS = ["intake", "training", "nutrition", "recovery"]

_TOOLKIT_BUILDERS = {
    "intake": build_intake_toolkit,
    "training": build_training_toolkit,
    "nutrition": build_nutrition_toolkit,
    "recovery": build_recovery_toolkit,
}


async def build_specialist(name: str) -> Agent:
    """构造一个专家 Agent。注意是 async，因为 toolkit 构造是 async。"""
    if name not in _SPECIALISTS:
        raise ValueError(f"Unknown specialist: {name}")

    # 关键：await 一次，拿到真正的 Toolkit 实例
    toolkit = await _TOOLKIT_BUILDERS[name]()

    return Agent(
        name=name.capitalize(),
        system_prompt=get_prompt(name),
        model=get_model(),
        toolkit=toolkit,
    )


async def build_all_specialists() -> dict[str, Agent]:
    return {name: await build_specialist(name) for name in _SPECIALISTS}