import inspect

from agentscope.tool import ToolChunk, ToolResponse
from agentscope.message import TextBlock

print("=" * 60)
print("ToolChunk.__init__:")
print(inspect.signature(ToolChunk.__init__))
print()
print("ToolChunk fields (annotations):")
print(getattr(ToolChunk, "__annotations__", {}))
print()
print("ToolChunk public methods:", [m for m in dir(ToolChunk) if not m.startswith("_")])
print()

print("=" * 60)
print("ToolResponse.__init__:")
print(inspect.signature(ToolResponse.__init__))
print()
print("ToolResponse fields (annotations):")
print(getattr(ToolResponse, "__annotations__", {}))
print()
print("ToolResponse public methods:", [m for m in dir(ToolResponse) if not m.startswith("_")])
print()

print("=" * 60)
print("TextBlock.__init__:")
print(inspect.signature(TextBlock.__init__))
print()

# 试着构造最简单的 ToolChunk
print("=" * 60)
print("试构造 ToolChunk:")
try:
    tc = ToolChunk(type="text", text="hello")
    print("  用 type/text:", type(tc).__name__)
except Exception as e:
    print("  type/text FAIL:", type(e).__name__, e)

try:
    tc = ToolChunk(content=[TextBlock(type="text", text="hello")])
    print("  用 content=[TextBlock]:", type(tc).__name__)
except Exception as e:
    print("  content=[TextBlock] FAIL:", type(e).__name__, e)

try:
    tc = ToolChunk()
    print("  空构造:", type(tc).__name__, "->", tc)
except Exception as e:
    print("  空构造 FAIL:", type(e).__name__, e)