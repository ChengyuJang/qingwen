import asyncio
import asyncio
import structlog
from agentscope.agent import Agent
from agentscope.mcp import MCPClient, StdioMCPConfig
from agentscope.tool import Toolkit
from app.agents.model import get_model

logger = structlog.get_logger("video_agent")

VIDEO_PROMPT = """你是「轻问」团队的视频推荐专家。
当用户需要学习某个训练动作、或者想找相关的跟练视频时，你可以调用 Bilibili 搜索工具，为用户推荐高质量的教学视频。

【工作流程】
1. 提取用户想找的动作名称或关键词（如"深蹲"、"练腿"）。
2. 调用 MCP 工具 `search_content` 搜索视频。
3. 从结果中挑选 1-3 个标题最相关、播放量高的视频。

【输出格式要求】
请必须使用 Markdown 的超链接格式输出视频，用户可以直接点击跳转。
格式必须严格遵循：
- [视频标题](https://www.bilibili.com/video/BV号)
- 一句话推荐理由
"""


async def build_video_agent() -> Agent:
    """构造带 B 站 MCP 工具的 Video Agent。"""
    try:
        mcp_client = MCPClient(
            name="bilibili",
            is_stateful=True,
            mcp_config=StdioMCPConfig(
                # 🔥 核心修改：直接调用已安装在系统里的命令，不再用 uvx
                command="astron-bilibili-mcp",
                args=[],
            ),
        )
        logger.info("connecting_bilibili_mcp_start")

        await asyncio.wait_for(mcp_client.connect(), timeout=15.0)
        logger.info("mcp_bilibili_connected")

        toolkit = Toolkit(mcps=[mcp_client])

        return Agent(
            name="Video",
            system_prompt=VIDEO_PROMPT,
            model=get_model(),
            toolkit=toolkit,
        )
    except Exception as e:
        logger.error("mcp_connect_failed", error=str(e))
        return Agent(
            name="Video",
            system_prompt="你是视频推荐专家，但当前视频搜索服务暂不可用，请直接引导用户去 B 站搜索对应动作。",
            model=get_model(),
        )