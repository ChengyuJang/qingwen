import inspect

from agentscope.agent import Agent

print("=" * 60)
print("Agent.__init__ signature:")
print(inspect.signature(Agent.__init__))
print()

print("Agent.__init__ is coroutine function?", inspect.iscoroutinefunction(Agent.__init__))
print()

print("Agent class methods:", [m for m in dir(Agent) if not m.startswith("_")])
print()

# 看 init 的文档
print("=" * 60)
print("Agent.__init__ docstring:")
print(inspect.getdoc(Agent.__init__))