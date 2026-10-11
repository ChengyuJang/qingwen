"""通义千问模型工厂。

所有 Agent 通过 get_model() 获取模型实例，避免在各处重复构造。
"""
import os

from agentscope.credential import DashScopeCredential
from agentscope.model import DashScopeChatModel

DEFAULT_MODEL = "qwen-plus"


def get_model(model_name: str = DEFAULT_MODEL) -> DashScopeChatModel:
    """返回一个配置好的通义千问模型实例。

    Args:
        model_name: 模型名，默认 qwen-plus。可选 qwen-turbo（更快更便宜）、
            qwen-max（更强但更贵）。
    """
    api_key = os.environ.get("DASHSCOPE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "DASHSCOPE_API_KEY 未设置。请检查系统环境变量，"
            "并完全重启 PyCharm 后再试。"
        )

    return DashScopeChatModel(
        credential=DashScopeCredential(api_key=api_key),
        model=model_name,
        stream=True,
    )