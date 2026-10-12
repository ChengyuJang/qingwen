"""Agent 可调用的工具函数。

约定：
- 每个工具是普通同步 Python 函数，入参用简单类型
- 返回 ToolChunk(content=[TextBlock(type="text", text=...)])
- 函数的 docstring 就是 LLM 看到的工具说明，务必写清楚
"""
from agentscope.message import TextBlock
from agentscope.tool import FunctionTool, ToolChunk, Toolkit


# ---------- 工具 1：体能计算 ----------
def fitness_calc(
    weight_kg: float,
    height_cm: float,
    age: int | None = None,
    gender: str | None = None,
    activity_level: str | None = None,
) -> ToolChunk:
    """计算用户的 BMI 与每日总消耗（TDEE）。

    Args:
        weight_kg: 体重（公斤）
        height_cm: 身高（厘米）
        age: 年龄，可选。TDEE 计算需要，若不提供只返回 BMI
        gender: 性别，"male" 或 "female"，可选。TDEE 计算需要
        activity_level: 活动水平，可选。取值：sedentary / light / moderate / active / very_active
    """
    lines: list[str] = []

    h_m = height_cm / 100.0
    bmi = weight_kg / (h_m * h_m)
    if bmi < 18.5:
        bmi_label = "偏瘦"
    elif bmi < 24:
        bmi_label = "正常"
    elif bmi < 28:
        bmi_label = "偏胖"
    else:
        bmi_label = "肥胖"
    lines.append(f"BMI = {bmi:.1f}（{bmi_label}）")

    if age is not None and gender in ("male", "female"):
        if gender == "male":
            bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
        else:
            bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

        factors = {
            "sedentary": 1.2,
            "light": 1.375,
            "moderate": 1.55,
            "active": 1.725,
            "very_active": 1.9,
        }
        factor = factors.get(activity_level or "moderate", 1.55)
        tdee = bmr * factor
        lines.append(f"BMR（基础代谢）= {bmr:.0f} kcal")
        lines.append(f"TDEE（每日总消耗，活动水平 {activity_level or 'moderate'}）= {tdee:.0f} kcal")

    return ToolChunk(content=[TextBlock(type="text", text="\n".join(lines))])


# ---------- 工具 2：动作库查询（占位，Phase 2.5 换 RAG） ----------
def search_exercise(
    target: str | None = None,
    equipment: str | None = None,
    keyword: str | None = None,
) -> ToolChunk:
    """按目标肌群、器械、关键词查询训练动作。

    Args:
        target: 目标肌群，如 "chest"（胸）、"back"（背）、"legs"（腿）、"core"（核心）、"full_body"（全身）
        equipment: 可用器械，如 "dumbbell"（哑铃）、"barbell"（杠铃）、"bodyweight"（徒手）
        keyword: 动作名关键词，如 "squat"、"卧推"
    """
    EXERCISES = [
        {"name": "杠铃深蹲", "target": "legs", "equipment": "barbell", "level": "intermediate"},
        {"name": "哑铃高脚杯深蹲", "target": "legs", "equipment": "dumbbell", "level": "beginner"},
        {"name": "哑铃罗马尼亚硬拉", "target": "legs", "equipment": "dumbbell", "level": "beginner"},
        {"name": "杠铃卧推", "target": "chest", "equipment": "barbell", "level": "intermediate"},
        {"name": "哑铃地板卧推", "target": "chest", "equipment": "dumbbell", "level": "beginner"},
        {"name": "哑铃单臂划船", "target": "back", "equipment": "dumbbell", "level": "beginner"},
        {"name": "引体向上", "target": "back", "equipment": "bodyweight", "level": "intermediate"},
        {"name": "平板支撑", "target": "core", "equipment": "bodyweight", "level": "beginner"},
    ]

    matched = []
    for e in EXERCISES:
        if target and e["target"] != target:
            continue
        if equipment and e["equipment"] != equipment:
            continue
        if keyword and keyword not in e["name"]:
            continue
        matched.append(e)

    if not matched:
        text = "未找到匹配的动作，请放宽查询条件。"
    else:
        text = "匹配到的动作：\n" + "\n".join(
            f"- {e['name']}（目标：{e['target']}，器械：{e['equipment']}，难度：{e['level']}）"
            for e in matched
        )

    return ToolChunk(content=[TextBlock(type="text", text=text)])

# ---------- 工具 3：RAG 知识库检索 ----------
async def search_knowledge(query: str, top_k: int = 5) -> ToolChunk:
    """在训练知识库中检索相关动作和训练科学知识。

    当用户问具体的训练动作、动作要点、组数次数、动作替换、某个肌群怎么练时，
    调用此工具检索权威知识，再基于检索结果回答。

    Args:
        query: 用户问题或需要检索的关键词，例如"哑铃练腿动作"、"膝盖不好怎么练腿"
        top_k: 返回条数，默认 5，最多 10
    """
    from app.db.session import AsyncSessionLocal
    from rag.retriever import search as rag_search

    top_k = max(1, min(top_k, 10))

    async with AsyncSessionLocal() as db:
        chunks = await rag_search(db, query, top_k=top_k, source="exercise_lib")

    if not chunks:
        return ToolChunk(
            content=[TextBlock(type="text", text="知识库中未找到相关内容。")]
        )

    lines = []
    for i, c in enumerate(chunks, 1):
        meta = c.metadata or {}
        lines.append(
            f"{i}. 【{c.title}】"
            f"（目标：{meta.get('target', '-')}，器械：{meta.get('equipment', '-')}，"
            f"相似度：{c.similarity:.2f}）\n{c.content}"
        )
    text_out = "\n\n".join(lines)
    return ToolChunk(content=[TextBlock(type="text", text=text_out)])



# ---------- Toolkit 构造（async，工具标记为只读以跳过权限确认） ----------
async def build_training_toolkit() -> Toolkit:
    t = Toolkit()
    await t.add_tool(FunctionTool(fitness_calc, is_read_only=True))
    await t.add_tool(FunctionTool(search_knowledge, is_read_only=True))
    return t


async def build_nutrition_toolkit() -> Toolkit:
    t = Toolkit()
    await t.add_tool(FunctionTool(fitness_calc, is_read_only=True))
    return t


async def build_intake_toolkit() -> Toolkit:
    return Toolkit()


async def build_recovery_toolkit() -> Toolkit:
    return Toolkit()