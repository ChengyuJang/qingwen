"""Agent 路由评估：验证 Orchestrator 是否正确派活。

每条测试 query 标注期望派给哪个（或哪些）专家，
跑 TeamPipeline 收集实际派活对象，对比计算路由准确率。

用法（在 backend/ 下）：
    python -m scripts.eval_routing
"""
import asyncio

from agentscope.event import EventType
from agentscope.message import UserMsg

from app.agents.team import build_team


# (query, 期望派给的专家集合)
TEST_CASES = [
    ("你好", set()),                                    # 纯打招呼，不派活
    ("我想开始健身", {"intake"}),                        # 信息不全，先采集
    ("我是新手，175cm 70kg，想减脂，家里有哑铃", {"training"}),  # 信息够，给方案
    ("每天该吃多少蛋白质", {"nutrition"}),
    ("我70kg想减脂，帮我算一下热量", {"nutrition"}),
    ("昨晚只睡了5小时，今天还能练吗", {"recovery"}),
    ("最近总觉得累，要不要降低训练强度", {"recovery"}),
    ("帮我推荐几个哑铃练胸的动作", {"training"}),
    ("我膝盖不好，怎么做深蹲", {"training"}),
    ("我想减脂，帮我制定训练和饮食计划", {"training", "nutrition"}),  # 多专家
    ("我想开始健身", {"intake"}),  # 无信息，采集
    ("我想增肌，帮我安排", {"intake"}),  # 无信息，采集
    ("能不能帮我订个机票", set()),                       # 超范围，不派活
    ("你是谁？能做什么", set()),                         # 自我介绍，不派活
]


async def route_one(pipe, query: str) -> set[str]:
    """跑一次，收集派活的专家名字集合。"""
    actual: set[str] = set()
    async for evt in pipe.reply_stream(UserMsg(name="user", content=query)):
        if evt.type == EventType.REPLY_START:
            agent = evt.name.lower()
            if agent != "orchestrator":
                actual.add(agent)
    return actual


async def main():
    print(f"路由评估：{len(TEST_CASES)} 条\n")

    correct = 0
    details = []

    for query, expected in TEST_CASES:
        pipe = await build_team()
        try:
            actual = await route_one(pipe, query)
        except Exception as e:
            actual = set()
            print(f"  [ERROR] {query}: {type(e).__name__}: {e}")

        # 判断标准：实际派活是期望集合的子集（允许少派，不允许错派）
        # 严格模式：完全相等
        is_exact = actual == expected
        # 宽松模式：实际是期望的子集（不多派给不该派的专家）
        is_subset = actual.issubset(expected) and len(actual) > 0 if expected else len(actual) == 0

        if is_exact:
            correct += 1

        details.append({
            "query": query,
            "expected": expected,
            "actual": actual,
            "exact": is_exact,
            "subset": is_subset,
        })

    n = len(TEST_CASES)
    print(f"{'='*60}")
    print(f"严格准确率（集合完全相等）: {correct/n:.3f}  ({correct}/{n})")
    subset_correct = sum(1 for d in details if d["subset"])
    print(f"宽松准确率（无错派专家）  : {subset_correct/n:.3f}  ({subset_correct}/{n})")
    print(f"{'='*60}\n")

    print("逐条明细：\n")
    for d in details:
        mark = "✅" if d["exact"] else ("🟡" if d["subset"] else "❌")
        print(f"{mark} {d['query']}")
        print(f"   期望：{sorted(d['expected']) or '(不派活)'}")
        print(f"   实际：{sorted(d['actual']) or '(不派活)'}")
        print()


if __name__ == "__main__":
    asyncio.run(main())