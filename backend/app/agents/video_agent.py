import asyncio
import structlog
import sys
from agentscope.agent import Agent
from agentscope.mcp import MCPClient, StdioMCPConfig
from agentscope.tool import Toolkit
from app.agents.model import get_model

logger = structlog.get_logger("video_agent")

VIDEO_PROMPT = """你是「轻问」团队的视频推荐专家。
当用户需要学习某个训练动作、或者想找相关的跟练视频时，你可以调用 Bilibili 搜索工具，为用户推荐高质量的教学视频。

【工作流程】
1. 提取用户想找的动作名称或关键词。
2. 调用 MCP 工具 `search_content` 搜索视频。
3. 把结果用 Markdown 格式输出，例如：[视频标题](url)
"""


async def build_video_agent() -> Agent:
    try:
        # 🔥 核心修改：直接启动我们本地写的脚本，不再走网络！
        mcp_client = MCPClient(
            name="bilibili",
            is_stateful=True,
            mcp_config=StdioMCPConfig(
                command=sys.executable,  # 当前环境的 python
                args=["-m", "app.agents.bilibili_mcp_server"],  # 启动本地脚本
            ),
        )

        await asyncio.wait_for(mcp_client.connect(), timeout=10.0)
        logger.info("mcp_bilibili_connected_success")

        toolkit = Toolkit(mcps=[mcp_client])

        return Agent(
            name="Video",
            system_prompt=VIDEO_PROMPT,
            model=get_model(),
            toolkit=toolkit,
        )
    except Exception as e:
        logger.error("mcp_connect_failed", error=str(e))
        # 降级兜底
        return Agent(
            name="Video",
            system_prompt="你是视频推荐专家，由于接口不可用，请直接给出 B站 搜索链接。",
            model=get_model(),
        )