import inspect

from agentscope.tool import Toolkit, Function, FunctionTool

print("=" * 60)
print("Function.__init__ signature:")
print(inspect.signature(Function.__init__))
print()

print("=" * 60)
print("FunctionTool.__init__ signature:")
print(inspect.signature(FunctionTool.__init__))
print()

print("=" * 60)
print("Function public methods:")
print([m for m in dir(Function) if not m.startswith("_")])
print()

print("=" * 60)
print("FunctionTool public methods:")
print([m for m in dir(FunctionTool) if not m.startswith("_")])
print()

# 试着用一个普通函数构造
def my_test_func(x: int, y: int) -> int:
    """加法测试。

    Args:
        x: 第一个数
        y: 第二个数
    """
    return x + y

print("=" * 60)
print("试着构造 Function:")
try:
    f = Function(my_test_func)
    print("  OK, type:", type(f).__name__)
    print("  has .name?", hasattr(f, "name"))
    if hasattr(f, "name"):
        print("  name:", f.name)
except Exception as e:
    print("  FAIL:", type(e).__name__, e)
print()

print("=" * 60)
print("试着构造 FunctionTool:")
try:
    ft = FunctionTool(my_test_func)
    print("  OK, type:", type(ft).__name__)
except Exception as e:
    print("  FAIL:", type(e).__name__, e)
print()

print("=" * 60)
print("试着把 Function 加到 Toolkit:")
try:
    t = Toolkit()
    f = Function(my_test_func)
    t.add_tool(f)
    print("  OK")
    print("  tool schemas:", t.get_tool_schemas())
except Exception as e:
    print("  FAIL:", type(e).__name__, e)