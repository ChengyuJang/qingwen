"""极简 B站视频搜索 MCP Server。
使用官方 mcp 库的 FastMCP，通过 Stdio 协议与主程序通信。
"""
import json
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Bilibili_Search")


@mcp.tool()
def search_content(keyword: str) -> str:
    """搜索 Bilibili 视频。

    Args:
        keyword: 搜索关键词，例如 "深蹲教学"
    """
    # 返回结构化的搜索链接，让 LLM 组装成 Markdown
    return json.dumps([
        {
            "title": f"B站搜索：{keyword}",
            "url": f"https://search.bilibili.com/all?keyword={keyword}",
            "author": "Bilibili"
        }
    ], ensure_ascii=False)


if __name__ == "__main__":
    mcp.run(transport="stdio")