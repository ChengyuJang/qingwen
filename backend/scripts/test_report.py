"""测试报告生成。用法：
    docker compose exec backend python -m scripts.test_report
"""
import asyncio
import json

from app.agents.report import generate_report


async def main():
    result = await generate_report(user_id=1, days=7)
    print("=" * 60)
    print("SUMMARY:", result["summary"])
    print("=" * 60)
    print("STATS:")
    print(json.dumps(result["content"]["stats"], ensure_ascii=False, indent=2, default=str))
    print("=" * 60)
    print("TEXT:")
    print(result["content"]["text"])


asyncio.run(main())