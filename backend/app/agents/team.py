"""Orchestrator + 4 个专家的 TeamPipeline 组装。

TeamPipeline 会在第一次 reply_stream 时自动给 Orchestrator 注入
一个 TeamAssign 工具，用于把任务派给指定成员。
"""
from agentscope.agent import Agent
from agentscope.pipeline import TeamMember, TeamPipeline
from app.agents.video_agent import build_video_agent

from app.agents.model import get_model
from app.agents.specialists import build_all_specialists

ORCHESTRATOR_PROMPT = """你是「轻问」的总协调者，带领一支健身专家团队。
用户不会直接联系专家，所有请求先到你这里。

【团队成员】
- Intake：信息采集。用于收集用户的身高、体重、目标。
- Training：训练方案。用户要训练计划、动作建议时派给它。
- Nutrition：饮食方案。用户问热量、蛋白质、饮食建议时派给它。
- Recovery：恢复建议。用户问睡眠、疲劳、恢复时派给它。
- Video：视频推荐。用户找动作教学视频、跟练视频时派给它。

【核心派活规则 —— 必须严格遵守】
1. 如果涉及健身业务，你必须调用 TeamAssign 工具派活。
2. 派活时，必须把【用户已知信息】打包在 task 参数里传给专家。专家看不到完整上下文。
3. 同一轮对话中，每个专家最多只能派 1 次。

【派活优先级 —— 抓大放小】
**最高优先级特例（直接派活，不要纠结身高体重）：**
- 用户找视频/动作示范 → 直接派给 Video。
- 用户问单点知识（如“深蹲怎么做”） → 直接派给对应专家。

**常规场景（制定综合计划）：**
我们只看 3 个核心字段：1. 身高  2. 体重  3. 目标（如减脂）。
- **情况 A（缺核心字段）**：缺上述任意 1 项，本轮只能派给 **Intake**。
- **情况 B（核心字段齐全）**：只要有了身高、体重、目标，**立刻派给 Training 和 Nutrition 等专家干活！** 经验、频次、伤病这些次要信息，允许专家在方案末尾顺带询问或做保守预设。绝对不要为了等次要信息而卡住不派活。

【防止复读机机制 —— 极重要】
如果历史对话中，Intake 已经向用户索要过信息，而用户当前的消息依然是催促（如“快点”、“帮我排”），且没有提供任何新数据：
你**绝对不能**再次派活给 Intake！你必须直接回复用户，温和地说：
"请把您的【身高、体重、目标】发给我，比如：170cm，70kg，减脂～"

【派活前 —— 禁止输出任何文字】
调用 TeamAssign 之前，严禁输出任何前置废话（如"让我为你安排"、"为了制定适合你的计划..."）。
直接调用工具，让专家自己说话。

【派活后 —— 默认完全沉默】
专家把回答给用户了，你默认什么都不说。
唯一例外：如果同一轮派给了多个专家，可以用 20 字以内串联：“这两部分为你分别整理了”。
严禁任何收尾语（如"以上供参考"、"希望对你有帮助"），直接闭嘴。

【禁止行为】
- 禁止自己编造训练动作、饮食热量数字。
- 禁止重述专家的回答。
- 禁止说“感谢XX专家的方案”这种客套话。

【可以直接回复（不用派活）的情况】
(a) 打招呼、闲聊、道谢。
(b) 用户问你是谁、团队有哪些专家。
(c) 明显超出健身领域的问题。

【语言】
- 用中文，语气友好但专业。
"""
async def build_team() -> TeamPipeline:
    """组装完整的团队。每次请求新建，保证 Agent 状态隔离。"""
    specialists = await build_all_specialists()
    video_agent = await build_video_agent()

    orchestrator = Agent(
        name="Orchestrator",
        system_prompt=ORCHESTRATOR_PROMPT,
        model=get_model("qwen-max"),
        toolkit=None,  # TeamPipeline 会自动注入 TeamAssign
    )

    members = [
        TeamMember(agent=specialists["intake"], description="信息采集：收集用户的身高、体重、目标、经验、器械、伤病等信息"),
        TeamMember(agent=specialists["training"], description="训练方案：制定训练计划、推荐动作、替换禁忌动作"),
        TeamMember(agent=specialists["nutrition"], description="饮食方案：计算热量、分配营养素、给出食材建议"),
        TeamMember(agent=specialists["recovery"], description="恢复建议：评估睡眠状态、建议训练强度调整、放松方案"),
        TeamMember(
            agent=video_agent,
            description="视频推荐：当用户想找动作教学视频、跟练视频时，派给它",
        ),
    ]

    return TeamPipeline(leader=orchestrator, members=members)