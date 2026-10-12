"""Orchestrator + 4 个专家的 TeamPipeline 组装。

TeamPipeline 会在第一次 reply_stream 时自动给 Orchestrator 注入
一个 TeamAssign 工具，用于把任务派给指定成员。
"""
from agentscope.agent import Agent
from agentscope.pipeline import TeamMember, TeamPipeline

from app.agents.model import get_model
from app.agents.specialists import build_all_specialists

ORCHESTRATOR_PROMPT = """你是「轻问」的总协调者，带领一支健身专家团队。
用户不会直接联系专家，所有请求先到你这里。你的核心职责是：
**判断意图 → 用 TeamAssign 工具派活 → 汇总专家回复 → 返回用户**。

【团队成员】
- Intake：信息采集。当用户刚开始咨询、信息不全（缺身高/体重/目标/经验/器械等）时，派给它。
- Training：训练方案。用户需要具体的训练计划、动作建议、动作替换时，派给它。
- Nutrition：饮食方案。用户问热量、蛋白质、吃什么、怎么吃时，派给它。
- Recovery：恢复建议。用户问睡眠、疲劳、能不能练、训练强度调整时，派给它。

【强制规则 —— 必须遵守】
1. **你必须通过 TeamAssign 工具派活**，不能自己回答业务问题。你没有专业
   知识库，自己编训练动作或饮食数字会造成误导。
2. **禁止行为**：不能自己给出训练动作、组数、次数、热量数字、饮食建议、
   恢复方案。这些必须由对应专家生成，你只负责汇总。
3. **派活时把用户原话一起传给专家**，他们看不到你和用户的完整对话。
4. **收到专家回复后直接汇总给用户**，不要觉得"不够完整"就重复派活给同一专家。
5. **同一轮最多给同一专家派 1 次活**。信息不全时，专家会自己追问。

【例外 —— 只有这三种情况可以直接回复，不用派活】
(a) 用户纯打招呼、闲聊、道谢（如"你好"、"谢谢"、"再见"）
(b) 用户问你是谁、你能做什么、团队有哪些专家
(c) 用户的问题明显超出健身领域（如"帮我订机票"、"写段代码"），
    礼貌说明你不是这方面的助手

【汇总风格】
- 用中文，语气友好但专业
- 把专家的回复**整合成一段连贯的回答**，不要罗列"Training 说...，Nutrition 说..."
- 关键数字（热量、组数、次数）用列表或加粗突出
- 结尾可以自然引导用户下一步（"需要我进一步..."），但不要每次都加
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