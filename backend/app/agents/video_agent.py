import structlog
from agentscope.agent import Agent
from app.agents.model import get_model

logger = structlog.get_logger("video_agent")

VIDEO_PROMPT = """你是「轻问」团队的视频推荐专家。
当用户需要学习某个训练动作、或者想找相关的跟练视频时，请为用户推荐高质量的教学视频。

【由于当前运行环境不支持 MCP 视频搜索接口，请你直接凭知识库推荐 B 站知名的动作教学视频】
请使用 Markdown 格式输出，例如：
- [深蹲教学（推荐搜索）](https://search.bilibili.com/all?keyword=深蹲教学)
- 一句话推荐理由
"""

async def build_video_agent() -> Agent:
    """构造 Video Agent（降级版，无 MCP 依赖，保证云端 100% 稳定）。"""
    logger.info("building_video_agent_fallback_mode")
    return Agent(
        name="Video",
        system_prompt=VIDEO_PROMPT,
        model=get_model(),
    )