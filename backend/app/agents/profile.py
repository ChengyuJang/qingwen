"""用户画像：从对话中抽取结构化信息，存入 user_profiles 表。"""
import json

import structlog
from agentscope.agent import Agent
from agentscope.message import UserMsg
from sqlalchemy import select

from app.agents.model import get_model
from app.db.models import UserProfile
from app.db.session import AsyncSessionLocal

logger = structlog.get_logger("profile")

EXTRACT_PROMPT = """你是信息抽取器。从给定的用户发言里提取健身相关信息。

【严格规则】
- 只提取用户**明确说过**的信息，禁止推测、脑补、假设
- 没提到的字段返回 null
- 只输出 JSON，不要任何其他文字、不要 markdown 代码块

【字段说明】
- height_cm: 身高厘米数（数字），如 175
- weight_kg: 体重公斤数（数字），如 70
- goal: 目标，只能是：减脂 / 增肌 / 塑形 / 健康 / 力量 / 体能
- experience_level: 经验，只能是：新手 / 进阶 / 专业
- weekly_frequency: 每周训练次数（数字）
- equipment: 器械列表，如 ["哑铃", "弹力带"]，没有则 null
- health_notes: 伤病或健康限制（字符串）
- gender: 性别，"male" 或 "female"

【示例输出】
{
  "height_cm": 175,
  "weight_kg": 70,
  "goal": "减脂",
  "experience_level": "新手",
  "weekly_frequency": 3,
  "equipment": ["哑铃"],
  "health_notes": null,
  "gender": "male"
}

无法确定的字段一律 null。"""


async def extract_profile(messages_text: str) -> dict:
    """从用户发言文本里抽取画像。失败返回空 dict。"""
    agent = Agent(
        name="ProfileExtractor",
        system_prompt=EXTRACT_PROMPT,
        model=get_model("qwen-plus"),  # 用快模型省成本
    )
    reply = await agent.reply(UserMsg(name="user", content=messages_text))
    text = reply.get_text_content().strip()

    # 剥离可能的 markdown 代码块
    if text.startswith("```"):
        text = text.split("```")[1] if "```" in text[3:] else text[3:]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    try:
        result = json.loads(text)
        if not isinstance(result, dict):
            return {}
        return result
    except Exception as e:
        logger.warning("profile_parse_failed", error=str(e), raw=text[:200])
        return {}


async def update_user_profile(user_id: int, messages_text: str) -> None:
    """抽取 + upsert 到 user_profiles（只覆盖有值的字段）。"""
    try:
        extracted = await extract_profile(messages_text)
    except Exception as e:
        logger.warning("profile_extract_failed", error=str(e))
        return

    # 过滤掉空值
    updates = {k: v for k, v in extracted.items() if v is not None}
    if not updates:
        return

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        if profile is None:
            profile = UserProfile(user_id=user_id)
            db.add(profile)

        # 只更新有值的字段
        for key in (
            "height_cm",
            "weight_kg",
            "goal",
            "experience_level",
            "weekly_frequency",
            "health_notes",
            "gender",
        ):
            if key in updates:
                setattr(profile, key, updates[key])

        if "equipment" in updates:
            profile.equipment = updates["equipment"]

        await db.commit()

    logger.info(
        "profile_updated",
        user_id=user_id,
        fields=list(updates.keys()),
    )