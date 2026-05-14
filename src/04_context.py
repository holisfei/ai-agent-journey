from os import name
import time

# 自定义额上下文管理器 context manager
# 实现 __enter__ 和 __exit__
class Timer:
    """自定义上下文耗时管理器"""
    def __init__(self, name: str):
        self.name = name
    
    # 实现 __enter__，返回实例
    def __enter__(self):
        self.start = time.perf_counter()
        return self

    # 实现 __exit__
    # exc_type：异常类型 exc_val：异常值 exc_tb：traceback
    # 执行没有异常的时候，以上参数都是None
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.perf_counter() - self.start
        print(f"{self.name} 耗时 {duration:.2f}s")
        return False
        # False 表示将错误抛出去
        # True 表示不抛出错误，内部自己处理异常

# 使用自定义的context manager，
# as t t就是 __enter__ 返回的实例
with Timer(name="sleep") as t: 
    time.sleep(1.0) # with 块内的逻辑执行完成之后,执行__exit__


# @contextmanager 装饰器 实现
from contextlib import contextmanager

@contextmanager # 使用装饰器
def timer(name: str):
    start = time.perf_counter()
    try:
        yield   # yield交出去 这里把控制权交给 with 块
    finally:    # finally总会被执行 所以 with 块执行完毕后，会执行这里
        duration = time.perf_counter() - start
        print(f"{name} 耗时 {duration:.2f}s")

with timer(name="contextmanager_timer") as t:
    time.sleep(1.0) # with 块内的逻辑执行完成之后 执行 finally

# LLM 调用统一收集日志
from loguru import logger
@contextmanager
def llm_call_context(model: str, request_id: str):
    """LLM 调用的统一上下文：日志、计时、错误捕获"""
    start = time.perf_counter()
    logger.info(f"[{request_id}] 请求了 {model}...")
    try:
        yield # 交给 with 块 执行请求 LLM 的逻辑
        # 到这里之后，说明 请求 LLM 成功
        duration = time.perf_counter() - start
        logger.info(f"[{request_id}] {model} 请求成功 耗时{duration:.2f}s")
    except Exception as e: # LLM 请求失败
        duration = time.perf_counter() - start # 记录耗时
        elapsed = time.perf_counter() - start
        logger.error(f"[{request_id}] {model} 请示失败 耗时:{duration:.2f}s 报错:{e}")
        raise e  # 抛出错误

with llm_call_context(model="gpt-4", request_id="125467"):
    # 模拟耗时请求 LLM 成功
    time.sleep(2.0) 
    # 请求成功了，继续执行 yield 之后的逻辑

    # 模拟耗时请求 LLM 失败
    # raise ConnectionError("连接超时") 
    # 请求失败了，继续执行 except 之后的逻辑

# 多个 with 语句可以并列
from pathlib import Path
import tempfile

context_dir = Path(tempfile.gettempdir()) / "com.python.learn" / "context"
context_dir.mkdir(parents=True, exist_ok=True)
context_file = context_dir / "manager.txt"
copy_file = context_dir / "copy.txt"

with(
    # w+，可读写，文件不存在会创建，且清空原内容
    # r+，可读写，文件必须存在 否则报错，且不会清空原来荣
    open(context_file, "w+", encoding="utf-8") as m_f,
    open(copy_file, "w+", encoding="utf-8") as c_f,
):
    m_f.write("hello manager")
    c_f.write("hello copy")
    # 关键一步：将光标移回文件开头，否则 read() 读不到刚写的内容
    m_f.seek(0)
    c_f.seek(0)
    print(m_f.read())
    print(c_f.read())

