"""周报/月报生成。

流程：
1. 从数据库聚合用户最近 N 天的数据（打卡、体重、规划）
2. 把统计数据喂给 LLM，生成人类可读的报告
3. 报告落库到 reports 表
"""
from collections import Counter
from datetime import datetime, timedelta, timezone
from app.db.models import DailyLog, Plan, Report, WeightRecord

import structlog
from agentscope.message import UserMsg
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import DailyLog, Plan, WeightRecord
from app.db.session import AsyncSessionLocal

logger = structlog.get_logger("report")

REPORT_PROMPT = """你是「轻问」的报告生成师。用户会给你一份结构化的数据统计，
你要把它转化成一份**温暖、有洞察、不说教**的个人健康报告。

【报告结构】
1. **本期概览**（2-3 句）：用自然的语言描述这个周期的整体表现。
   给出一个印象式的总结，而不是罗列数字。
2. **亮点**（如果有）：肯定用户做得好的地方，具体到数据。
3. **趋势与洞察**：从数据里读出故事。比如：
   - 睡眠和训练的关系
   - 体重的变化节奏（不要只看绝对数值）
   - 训练频率是否稳定
4. **下期建议**（2-3 条，具体可执行）：不要说"保持运动"这种废话。

【语气】
- 温和、诚实、不制造焦虑
- 不要用"自律即自由"这类口号
- 不要因为数据差就批评，用"这可能说明…"的表达
- 用中文

【数据缺失的处理】
- 某个维度数据太少时，坦诚说明，不要强行解读
- 整个周期没有任何数据时，直接说"这一期没有记录，从下一期开始吧"
"""


async def aggregate_user_data(
    db: AsyncSession, user_id: int, days: int
) -> dict:
    """聚合用户最近 N 天的数据。"""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    # 1) 打卡数据
    log_result = await db.execute(
        select(DailyLog).where(
            DailyLog.user_id == user_id, DailyLog.log_date >= since
        )
    )
    logs = log_result.scalars().all()

    trained_days = sum(1 for log in logs if log.trained)
    sleep_values = [log.sleep_hours for log in logs if log.sleep_hours is not None]
    avg_sleep = round(sum(sleep_values) / len(sleep_values), 1) if sleep_values else None
    mood_counter = Counter(log.mood for log in logs if log.mood)
    top_moods = mood_counter.most_common(3)

    # 2) 体重
    weight_result = await db.execute(
        select(WeightRecord)
        .where(WeightRecord.user_id == user_id, WeightRecord.record_date >= since)
        .order_by(WeightRecord.record_date.asc())
    )
    weights = weight_result.scalars().all()
    weight_start = weights[0].weight_kg if weights else None
    weight_end = weights[-1].weight_kg if weights else None
    weight_change = (
        round(weight_end - weight_start, 1)
        if weight_start is not None and weight_end is not None
        else None
    )

    # 3) 规划数
    plan_result = await db.execute(
        select(Plan.kind, func.count(Plan.id))
        .where(Plan.user_id == user_id, Plan.created_at >= since)
        .group_by(Plan.kind)
    )
    plan_counts = {kind: cnt for kind, cnt in plan_result.all()}

    return {
        "period_days": days,
        "log_count": len(logs),
        "trained_days": trained_days,
        "avg_sleep_hours": avg_sleep,
        "top_moods": top_moods,
        "weight_records": len(weights),
        "weight_start": weight_start,
        "weight_end": weight_end,
        "weight_change": weight_change,
        "plan_counts": plan_counts,
    }


def format_stats_for_llm(stats: dict) -> str:
    """把统计数据格式化成给 LLM 读的文本。"""
    lines = [f"周期：最近 {stats['period_days']} 天"]
    lines.append(f"打卡条数：{stats['log_count']}")
    lines.append(f"训练天数：{stats['trained_days']}")

    if stats["avg_sleep_hours"] is not None:
        lines.append(f"平均睡眠：{stats['avg_sleep_hours']} 小时")
    else:
        lines.append("睡眠数据：无")

    if stats["top_moods"]:
        moods_str = "、".join(f"{m}（{c}次）" for m, c in stats["top_moods"])
        lines.append(f"主要心情：{moods_str}")
    else:
        lines.append("心情数据：无")

    if stats["weight_records"] > 0:
        lines.append(
            f"体重记录：{stats['weight_records']} 条，"
            f"从 {stats['weight_start']}kg 到 {stats['weight_end']}kg，"
            f"变化 {stats['weight_change']:+}kg"
        )
    else:
        lines.append("体重数据：无")

    if stats["plan_counts"]:
        plans_str = "、".join(f"{k} {v} 份" for k, v in stats["plan_counts"].items())
        lines.append(f"生成的规划：{plans_str}")
    else:
        lines.append("规划数据：无")

    return "\n".join(lines)


async def generate_report(
    user_id: int, days: int = 7, kind: str = "weekly"
) -> Report:
    """生成一份报告并落库，返回 Report 对象。"""
    async with AsyncSessionLocal() as db:
        stats = await aggregate_user_data(db, user_id, days)

    stats_text = format_stats_for_llm(stats)

    # 数据全空：直接返回提示，不调 LLM
    if stats["log_count"] == 0 and stats["weight_records"] == 0:
        text = (
            "这一期没有任何打卡或体重记录。从下一期开始，"
            "试着每天花 1 分钟记录一下，我们就可以看到你的节奏了。"
        )

        return await _save_report(user_id, kind, days, stats, text, "这一期没有记录")

    # 调 LLM 生成报告
    # 调 LLM 生成报告
    from agentscope.agent import Agent
    from app.agents.model import get_model

    agent = Agent(
        name="Reporter",
        system_prompt=REPORT_PROMPT,
        model=get_model("qwen-max"),
    )

    user_msg = UserMsg(
        name="user",
        content=f"请根据以下数据生成一份报告：\n\n{stats_text}",
    )

    reply = await agent.reply(user_msg)
    text = reply.get_text_content()

    # 一句话总结：跳过 Markdown 标题，取第一段正文
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    content_lines = [line for line in lines if not line.startswith("#")]
    summary = content_lines[0][:80] if content_lines else text[:80]

    return await _save_report(user_id, kind, days, stats, text, summary)

async def _save_report(
    user_id: int,
    kind: str,
    days: int,
    stats: dict,
    text: str,
    summary: str,
) -> Report:
    """把生成的报告落库。"""
    period_end = datetime.now(timezone.utc)
    period_start = period_end - timedelta(days=days)

    async with AsyncSessionLocal() as db:
        report = Report(
            user_id=user_id,
            kind=kind,
            period_start=period_start,
            period_end=period_end,
            summary=summary,
            content={"stats": stats, "text": text},
        )
        db.add(report)
        await db.commit()
        await db.refresh(report)
        logger.info(
            "report_generated",
            user_id=user_id,
            kind=kind,
            days=days,
            report_id=report.id,
        )
        return report