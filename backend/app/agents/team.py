"""Orchestrator + 4 个专家的 TeamPipeline 组装。

TeamPipeline 会在第一次 reply_stream 时自动给 Orchestrator 注入
一个 TeamAssign 工具，用于把任务派给指定成员。
"""
from agentscope.agent import Agent
from agentscope.pipeline import TeamMember, TeamPipeline

from app.agents.model import get_model
from app.agents.specialists import build_all_specialists

ORCHESTRATOR_PROMPT = """你是「轻问」的总协调者，带领一支健身专家团队。
用户不会直接联系专家，所有请求先到你这里。你的职责是判断用户意图，
把任务派给合适的专家，最后把专家的回复整合后返回用户。

【团队成员】
- Intake：信息采集。当用户刚开始咨询、信息不全（缺身高/体重/目标/经验/器械等）时，派给它。
- Training：训练方案。用户需要具体的训练计划、动作建议、动作替换时，派给它。
- Nutrition：饮食方案。用户问热量、蛋白质、吃什么、怎么吃时，派给它。
- Recovery：恢复建议。用户问睡眠、疲劳、能不能练、训练强度调整时，派给它。

【工作规则】
1. 用 TeamAssign 工具派活，一次可以派给多个成员（它们会并行执行）。
2. 派活时把必要的上下文写清楚，成员看不到你和用户的完整对话。
3. 用户一句话可能涉及多个领域（如"帮我减脂"需要 Training + Nutrition），
   判断需要几位专家后一次性派出。
4. 收到成员回复后，整合成一段连贯、友好的回答给用户。不要罗列"Training 说...，
   Nutrition 说..."，直接自然地组织成一份完整建议。
5. 如果用户只是闲聊、打招呼、问你是谁，直接回复，不用派活。
6. 如果问题超出健身领域（如订机票、写代码），礼貌说明你不是这方面的助手。

【回答风格】
- 用中文，语气友好但专业
- 结论先行，细节在后
- 关键数字（热量、组数、次数）用列表或加粗突出
"""


async def build_team() -> TeamPipeline:
    """组装完整的团队。每次请求新建，保证 Agent 状态隔离。"""
    specialists = await build_all_specialists()

    orchestrator = Agent(
        name="Orchestrator",
        system_prompt=ORCHESTRATOR_PROMPT,
        model=get_model(),
        toolkit=None,  # TeamPipeline 会自动注入 TeamAssign
    )

    members = [
        TeamMember(agent=specialists["intake"], description="信息采集：收集用户的身高、体重、目标、经验、器械、伤病等信息"),
        TeamMember(agent=specialists["training"], description="训练方案：制定训练计划、推荐动作、替换禁忌动作"),
        TeamMember(agent=specialists["nutrition"], description="饮食方案：计算热量、分配营养素、给出食材建议"),
        TeamMember(agent=specialists["recovery"], description="恢复建议：评估睡眠状态、建议训练强度调整、放松方案"),
    ]

    return TeamPipeline(leader=orchestrator, members=members)