"""从 AgentScope 事件流里提取 LLM/工具调用的观测数据。

每个请求的 SSE 生成器里收集，请求结束时统一打日志。
"""
import time
from dataclasses import dataclass, field

import structlog

logger = structlog.get_logger("llm")


@dataclass
class CallStats:
    agent: str
    started_at: float
    input_tokens: int = 0
    output_tokens: int = 0
    finished_reason: str = ""


@dataclass
class ToolStats:
    agent: str
    tool_name: str
    started_at: float
    duration_ms: float = 0.0
    state: str = "unknown"


@dataclass
class RequestTrace:
    """一次 /chat/stream 请求的完整调用追踪。"""
    request_id: str
    llm_calls: list[CallStats] = field(default_factory=list)
    tool_calls: list[ToolStats] = field(default_factory=list)
    agents_involved: set[str] = field(default_factory=set)

    # 内部：reply_id → 正在进行的 CallStats
    _pending_llm: dict[str, CallStats] = field(default_factory=dict)
    # 内部：tool_call_id → ToolStats
    _pending_tools: dict[str, ToolStats] = field(default_factory=dict)

    def on_reply_start(self, reply_id: str, agent: str) -> None:
        self.agents_involved.add(agent)

    def on_model_call_start(self, reply_id: str, agent: str) -> None:
        self._pending_llm[reply_id] = CallStats(agent=agent, started_at=time.perf_counter())

    def on_model_call_end(
        self,
        reply_id: str,
        input_tokens: int,
        output_tokens: int,
        finished_reason: str,
    ) -> None:
        stats = self._pending_llm.pop(reply_id, None)
        if stats is None:
            return
        stats.input_tokens = input_tokens
        stats.output_tokens = output_tokens
        stats.finished_reason = finished_reason
        self.llm_calls.append(stats)

    def on_tool_call_start(self, tool_call_id: str, agent: str, tool_name: str) -> None:
        self._pending_tools[tool_call_id] = ToolStats(
            agent=agent, tool_name=tool_name, started_at=time.perf_counter()
        )

    def on_tool_result_end(self, tool_call_id: str, state: str) -> None:
        stats = self._pending_tools.pop(tool_call_id, None)
        if stats is None:
            return
        stats.duration_ms = round((time.perf_counter() - stats.started_at) * 1000, 1)
        stats.state = state
        self.tool_calls.append(stats)

    def emit(self) -> None:
        """请求结束时调用，输出汇总日志。"""
        total_in = sum(c.input_tokens for c in self.llm_calls)
        total_out = sum(c.output_tokens for c in self.llm_calls)

        logger.info(
            "chat_completed",
            request_id=self.request_id,
            agents=sorted(self.agents_involved),
            llm_calls=len(self.llm_calls),
            tool_calls=len(self.tool_calls),
            total_input_tokens=total_in,
            total_output_tokens=total_out,
        )

        # 逐个 LLM 调用明细
        for c in self.llm_calls:
            logger.debug(
                "llm_call",
                request_id=self.request_id,
                agent=c.agent,
                input_tokens=c.input_tokens,
                output_tokens=c.output_tokens,
                duration_ms=round((time.perf_counter() - c.started_at) * 1000, 1),
                finished_reason=c.finished_reason,
            )

        # 逐个工具调用明细
        for t in self.tool_calls:
            logger.info(
                "tool_call",
                request_id=self.request_id,
                agent=t.agent,
                tool=t.tool_name,
                duration_ms=t.duration_ms,
                state=t.state,
            )