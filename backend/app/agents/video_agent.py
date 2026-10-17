import structlog
from agentscope.agent import Agent
from agentscope.mcp import MCPClient, StdioMCPConfig
from agentscope.tool import Toolkit
from app.agents.model import get_model

logger = structlog.get_logger("video_agent")

VIDEO_PROMPT = """你是「轻问」团队的视频推荐专家。
当用户需要学习某个训练动作、或者想找相关的跟练视频时，你可以调用 Bilibili 搜索工具，为用户推荐高质量的教学视频。

【工作流程】
1. 提取用户想找的动作名称或关键词（如“深蹲”、“练腿”）。
2. 调用 `search_content` 工具搜索视频。
3. 从结果中挑选 1-3 个标题最相关、播放量高的视频。
4. 用友好的语气回复，直接给出视频标题和 BVID，方便用户去搜索。
"""

async def build_video_agent() -> Agent:
    """构造一个带 B 站 MCP 工具的 Video Agent。"""
    try:
        # 1. 配置并连接 StdIO MCP Server
        # 这里使用 uvx 自动拉取并运行 astron-bilibili-mcp
        mcp_client = MCPClient(
            name="bilibili",
            is_stateful=True,
            mcp_config=StdioMCPConfig(
                command="uvx",
                args=["--from", "astron-bilibili-mcp", "astron-bilibili-mcp"],
            ),
        )
        await mcp_client.connect()
        logger.info("mcp_bilibili_connected")

        # 2. 把 MCP 挂载到 Toolkit
        toolkit = Toolkit(mcps=[mcp_client])

        # 3. 创建 Video Agent
        return Agent(
            name="Video",
            system_prompt=VIDEO_PROMPT,
            model=get_model(),
            toolkit=toolkit,
        )
    except Exception as e:
        logger.error("mcp_connect_failed", error=str(e))
        # 如果 MCP 连不上，退化成无工具的普通 Agent，避免整个系统崩溃
        return Agent(
            name="Video",
            system_prompt="你是视频推荐专家，但当前视频搜索服务不可用，请引导用户自行去 B 站搜索。",
            model=get_model(),
        )