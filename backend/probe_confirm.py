import inspect

from agentscope.agent import Agent

print("=" * 60)
print("Agent.reply_stream 签名:")
print(inspect.signature(Agent.reply_stream))
print()

print("=" * 60)
print("Agent.reply 签名:")
print(inspect.signature(Agent.reply))
print()

print("=" * 60)
print("Agent public 方法:")
print([m for m in dir(Agent) if not m.startswith("_")])
print()

print("=" * 60)
print("Agent.handle_confirm 存在?", hasattr(Agent, "handle_confirm"))
for name in dir(Agent):
    if "confirm" in name.lower() or "permission" in name.lower():
        print(f"  找到: {name}")