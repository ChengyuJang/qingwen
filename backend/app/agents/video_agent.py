import structlog
import json
from agentscope.agent import Agent
from agentscope.tool import Toolkit, FunctionTool
from agentscope.message import TextBlock
from agentscope.tool import ToolChunk

from app.agents.model import get_model

logger = structlog.get_logger("video_agent")

VIDEO_PROMPT = """你是「轻问」团队的视频推荐专家。
当用户需要学习某个训练动作、或者想找相关的跟练视频时，你可以调用 `search_video` 工具，为用户推荐高质量的教学视频。

【工作流程】
1. 提取用户想找的动作名称或关键词。
2. 调用工具 `search_video` 搜索视频。
3. 把结果用 Markdown 格式输出，例如：[视频标题](url)
"""


def search_video(keyword: str) -> ToolChunk:
    """搜索 Bilibili 视频。

    Args:
        keyword: 搜索关键词，例如 "深蹲教学"
    """
    # 这里直接构造返回结果
    result_json = json.dumps([
        {
            "title": f"B站搜索：{keyword}",
            "url": f"https://search.bilibili.com/all?keyword={keyword}",
            "author": "Bilibili"
        }
    ], ensure_ascii=False)

    return ToolChunk(content=[TextBlock(type="text", text=result_json)])


async def build_video_agent() -> Agent:
    """构造 Video Agent（使用本地 FunctionTool 替代 MCPClient，绝对稳定）。"""
    try:
        toolkit = Toolkit()
        # 把我们的搜索函数注册为工具
        await toolkit.add_tool(FunctionTool(search_video, is_read_only=True))

        logger.info("video_agent_initialized_with_local_tool")

        return Agent(
            name="Video",
            system_prompt=VIDEO_PROMPT,
            model=get_model(),
            toolkit=toolkit,
        )
    except Exception as e:
        logger.error("video_agent_init_failed", error=str(e))
        # 终极降级兜底
        return Agent(
            name="Video",
            system_prompt="你是视频推荐专家，由于接口不可用，请直接给出 B站 搜索链接。",
            model=get_model(),
        )