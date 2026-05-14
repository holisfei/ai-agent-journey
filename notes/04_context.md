# with 语法是什么？
- 用途：保证「成对操作」中的退出动作一定执行
- 和 Swift 对照：相当于 defer
- 应用场景：文件、锁、连接、事务、计时、日志上下文...
    - 文件打开 open() as f 的模式（r/w/a/x + b/t/+）

```python
# 1. 文件
with open("a.txt") as f:
    # 执行逻辑
    do_something
# 自动关闭

# 2. 锁（多线程同步）
import threading
lock = threading.Lock()
with lock:
    # 临界区代码，自动获取锁、自动释放
    shared_data += 1

# 3. 数据库连接 / 事务
with db.transaction():
    db.execute("INSERT ...")
# 异常时自动 rollback，正常时自动 commit

# 4. HTTP 客户端（下周 asyncio 就要用）
import httpx
with httpx.Client() as client:
    response = client.get(url)
# 自动释放连接池

# 5. 临时切换工作目录
import os
from contextlib import chdir
with chdir("/tmp"):
    # 这里 cwd 是 /tmp
    ...
# 退出后自动恢复

# 6. 计时
with timer():
    do_something()
# 自动打印耗时

# 7. 异常抑制
from contextlib import suppress
with suppress(FileNotFoundError):
    os.remove("maybe_exists.txt")
```

# 下文管理器 contextmanager
- 方法 1：类 + __enter__/__exit__
    - __enter__(self) 返回了实例，as后的别名就是这里返回的实例
    - __exit__(self, exc_type, exc_val, exc_tb)始终都会被执行
- 方法 2：@contextmanager 装饰器（推荐）
- 关键点：异常处理、返回值绑定

自定义实现contextmanager：

```python
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
    time.sleep(1.0) # with 块内的逻辑执行完成之后
```

# 嵌套与多重 with

```python
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
```

# 异步上下文管理器

```async with、@asynccontextmanager```

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def async_timer(name: str):
    start = time.perf_counter()
    try:
        yield
    finally:
        print(f"[{name}] took {time.perf_counter() - start:.3f}s")

# 用
async def main():
    async with async_timer("api_call"):
        await some_async_call()
```

# 实战示例
- timer 计时器
- LLM 调用上下文
@contextmanager 装饰器 实现：
```python
# @contextmanager 装饰器 实现
from contextlib import contextmanager

@contextmanager # 使用装饰器
def timer(name: str):
    start = time.perf_counter()
    try:
        yield   # yield交出去 这里把控制权交给 with 块
    finally:    # with 块执行完毕后，才会执行这里
        duration = time.perf_counter() - start
        print(f"{name} 耗时 {duration:.2f}s")

with timer(name="contextmanager_timer") as t:
    time.sleep(1.0) # with 块内的逻辑执行完成之后 执行 finally
```

模拟调用 LLM 统一收集日志逻辑：
```python
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
```

# Anki 卡片 

```python
Q: with 语法的核心保证是什么？
A: 退出动作一定执行（即使中间抛异常）

Q: Python 中相当于 Swift defer 的机制是？
A: 上下文管理器 + with 语法

Q: 类实现上下文管理器需要哪两个方法？
A: __enter__ 和 __exit__

Q: __enter__ 返回值绑定到哪里？
A: with ... as 后面的变量

Q: __exit__ 返回 True 表示什么？
A: 吞掉异常，不向上抛

Q: 写上下文管理器的简洁方式？
A: @contextlib.contextmanager + yield

Q: 现代化路径处理推荐用什么？
A: pathlib.Path（用 / 拼接，重载运算符）

Q: Path 一行读文件的方法？
A: path.read_text(encoding="utf-8")
```