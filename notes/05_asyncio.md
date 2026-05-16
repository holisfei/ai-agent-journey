# asyncio 基础

### 1. 协程(Coroutine)

函数执行过程中，可以主动"赞停"，将控制权出去，等会儿再回来继续执行，python用 ```async def```来表示一个协程函数

### 2. 事件循环（Event Loop）：

维护了一个任务队列，类似于dart的时间驱动循环机制，不停的循环检查任务的执行状态。

### 3. awit（等待）

这是”协程“的暂停开关，告诉事件循环：当前任务比较耗时，先将资源给别的任务，等耗时任务执行完毕后，再回来处理后续逻辑。

模拟协程并发操作：

```python
import asyncio
import os
import time

# 定义协程函数
async def boil_water():
    print("开始烧水")
    # await 模拟异步耗时操作
    # 事情循环机制会并发执行别的任务，不会卡在这里
    await asyncio.sleep(3.0)
    print("水烧开了")

async def cut_vegetables():
    print("开始切菜")
    # await 模拟异步耗时操作
    await asyncio.sleep(2.0)
    print("菜切好了")

async def cook():
    # 创建 协程任务 - asyncio.create_task
    task1 = asyncio.create_task(boil_water())
    task2 = asyncio.create_task(cut_vegetables())
    # 执行 协程任务
    await task1
    await task2

start = time.perf_counter()
# asyncio.run() 会启动事件循环，并运行协程函数cook
asyncio.run(cook())
print(f"耗时{time.perf_counter() - start}s") # 3s
```

- 使用```async def```来创建一个协程函数
- 使用```await```告诉事件循环，先去处理别的任务，不用卡着这里
- 使用```asyncio.create_task```创建了一个协程任务
    - 没有用```asyncio.create_task```包裹的 await，任务不会并发执行，而是同步执行
    - ```asyncio.create_task```让任务先执行，然后再```await```结果
- 使用```asyncio.run```启动运行一个协程任务，底层由事件循环驱动

### 事件循环是单线程

如果你在协程里调用了传统的阻塞式同步代码（比如 time.sleep()、普通的 requests 库、或者繁重的 CPU 计算），整个事件循环就会被卡死！所有其他的协程都得跟着一起等。

所以在```asyncio```的世界里需要使用支持异步的代码和三方库：
- 网络请求不要用 ```requests```，要用 ```httpx``` 或 ```aiohttp```
- 睡觉不要用 ```time.sleep()```，要用 ```asyncio.sleep()```
- 数据库操作要用 ```databases、asyncpg``` 等异步驱动

# asyncio 进阶

### asyncio.gather() 并发执行任务 结果统一返回

使用```asyncio.gather()```来将所有协程函数一次性加入协程任务（底层也是调用了```asyncio.create_task```）
- 任务并发执行：协程任务会并发执行
- 结果统一返回：等所有任务都执行完成之后，将每个协程函数的返回值包装进 list 返回
    - list 结果的顺序就是任务加入时候的顺序
- 某一个任务失败，其余任务继续执行，但是拿不到执行结果
    - return_exceptions = True，失败的任务作为普通返回值返回，而不是不返回

```python
async def gather_cook():
    # 直接把多个协程丢进 gather，它们会并发执行
    result = await asyncio.gather(
        boil_water(),
        cut_vegetables(),
        return_exceptions = True
    )
    # 返回结果list 顺序会严格按照传入 gather 的顺序返回
    print(f"gather_cook 并发执行完成 {result}")
start = time.perf_counter()
asyncio.run(gather_cook())
print(f"gather_cook耗时{time.perf_counter() - start}s")
```

### asyncio.as_completed 并发执行任务 结果一个一个返回

```asyncio.as_completed```也会执行并发任务，但是任务的执行结果是哪个执行完成后立马返回，而不是等到所有任务都执行完成后统一返回执行结果

```py
async def completed_cook():
    for coro in asyncio.as_completed([boil_water(), cut_vegetables()]):
        result = await coro
        print(f"as_completed 并发执行完成结果 {result}")
asyncio.run(completed_cook())
```

### asyncio.TaskGroup 某一个任务失败 取消所有

```TaskGroup```组织的任务和```gather```比，区别有：
- 只要有一个任务失败，那所有的任务都会取消，终结所有任务
- 资源清理保证：通过 ```async with``` 上下文，所有任务一定被妥善处理
- 错误聚合：多个错误用 ```ExceptionGroup``` 统一抛出（Python 3.11+ 新特性）

```gather```只在明确想要【失败的任务不影响其他任务执行】

```py
async def group_cook():
    async with asyncio.TaskGroup() as tg:
        task1 = tg.create_task(cut_vegetables())
        task2 = tg.create_task(boil_water())
        task3 = tg.create_task(fail_task()) # 任务失败，取消所有
        
        result1 = await task1
        result2 = await task2
        result3 = await task3

        print(f"group_cook 结果{result1}")
        print(f"group_cook 结果{result2}")
        print(f"group_cook 结果{result3}")
asyncio.run(group_cook())  
```

### asyncio.wait_for 超时控制

协程任务在执行的过程中难免会执行时间太长，所以
asyncio.wait_for 可以给一个协程函数设置超时时间，超时抛出异常

```python
async def timeout_process():
    print("开始加载")
    await asyncio.sleep(5.0)
    print("加载成功")

async def http_wait_for():
    try:
        result = await asyncio.wait_for(timeout_process(), timeout=2)
    except Exception as e:
        print(f"请求超时:{e}")

asyncio.run(http_wait_for())
```

### asyncio.Semaphore

比如在爬虫场景下，我们不能一次性同时爬取太多数据请求，这样会被当做攻击对象
，asyncio.Semaphore 限制同一时间只能有固定数量的任务在运行

```py
semaphore = asyncio.Semaphore(3) # 同时只能执行3个任务
async def constrained_task(id: int):
    print(f"开始执行semaphore")
    # with语句，自动处理获取和释放信号量
    async with semaphore:
        print(f"🚀 任务{id} 正在执行 (当前并发数: 3)")
        await asyncio.sleep(3)
        print(f"🚀 任务{id} 完成了")

async def task_semaphore():
    # 一次创建5个协程任务
    result = await asyncio.gather(
        constrained_task(id=1),
        constrained_task(id=2),
        constrained_task(id=3),
        constrained_task(id=4),
        constrained_task(id=5)
    )
    print(result)

asyncio.run(task_semaphore())
```

### asyncio.CancelledError 取消任务与资源清理

对于一个耗时过长的任务，可以被取消终止执行，在 asyncio 中，取消任务不是简单的杀掉任务，而是通过抛出 asyncio.CancelledError 异常来通知协程，让它有机会做最后的清理工作（比如关闭文件、回滚数据库事务）。

```py
async def long_task():
    try:
        print("long_task任务开始请求")
        await asyncio.sleep(6.0)
    except asyncio.CancelledError:
        print(f"long_task任务执行中断, 做其余清理/保存动作")
        raise # 继续向上抛异常

async def cancel_task():
    task = asyncio.create_task(long_task())
    await asyncio.sleep(3)
    task.cancel() # 取消任务
    try:
        await task
    except asyncio.CancelledError as e:
        print(f"cancel_task异常：{e}")

asyncio.run(cancel_task())
```

### async with 异步自动执行

就像我们用 with open() 打开文件会自动关闭一样，在异步编程中，很多资源（比如 aiohttp、httpx的网络会话、异步数据库连接池）也需要自动释放。这就用到了 async with。

```py
import httpx
import asyncio

async def fetch_url(url):
    # 使用 AsyncClient，并配合 async with 自动管理连接池的开启和关闭
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        print("异步请求完成，状态码：", response.status_code)

async def main():
    status = await fetch_url("https://www.example.com")
    print(f"网站状态码: {status}")

asyncio.run(main()) 
```

# httpx

httpx是网络请求库，其基本用法有:
```py
# header
headers = {
    "Accept": "application/json"
}
# 连接10s超时，读取数据15s超时，写数据30s超时，pool连接池60s超时
timeout = httpx.Timeout(
    connect=10, 
    read=15, 
    write=30,
    pool=60
)
# 最大连接数是100，其中保活连接最大20
limit = httpx.Limits(
    max_connections=100, 
    max_keepalive_connections=20
)

# 全局复用连接池，复用连接池，提高并发请求性能

# AsyncClient为异步client
client = httpx.AsyncClient(
    timeout=timeout, 
    limits=limit, 
    headers=headers
)

# 同步client
client_sync = httpx.Client(
    timeout=timeout, 
    limits=limit, 
    headers=headers
)

# 普通请求
res = await client.get(url)

# streaming 流式请求
async with client.stream("GET", url) as resp:
        async for chunk in resp.aiter_text():
                print(chunk, end="", flush=True)
    
```

对于简单的普通请求可以不用async with来自动管理上下文的连接池，但是对于流式请求必须使用async with来自动管理来释放连接池

# loguru日志库

### 基本用法
```py
logger.debug("这是一条调试信息")
logger.info("程序正常运行中")
logger.warning("需要注意的警告")
logger.error("发生了错误")
logger.success("操作成功完成！")  # Loguru 独有的 SUCCESS 级别
```
日志轮转配置：
```py
# 写入文件，并且每天凌晨自动切割，只保留最近 7 天的日志
# enqueue=True 开启异步队列写入
logger.add("logs/2026/app_{time}.log", rotation="00:00", retention="7 days", encoding="utf-8", enqueue=True )

# 或者按文件大小切割（比如达到 100MB 就生成新文件），并自动压缩旧日志
# logger.add("logs/2026/app_{time}.log", rotation="100 MB", compression="zip")
```
- rotation：支持按时间（"daily", "00:00"）或大小（"500 MB"）轮转。
- retention：自动清理过期的日志文件（如 "10 days", "5" 表示保留5个文件）。

### 异常捕获
```py
# 自动捕获异常
@logger.catch 
def divid(x:int, y:int):
    x/y
# 发生异常时，会自动捕获并记录完整的堆栈和变量值
divid(x=1, y=0)

# 手动捕获异常
try:
    1/0
except Exception:
    logger.exception("发生了一个除零异常")
```

# asyncio.run() 的执行时机

asyncio.run()不应该被频繁调用，只需要在程序的主入口去调用1次就行

```py
async def main():
    # 在这里执行 协程函数(await)和普通函数
    await cook()
    print(f"耗时{time.perf_counter() - start}s")

    start = time.perf_counter()
    await gather_cook()
    print(f"gather_cook耗时{time.perf_counter() - start}s") 

    await completed_cook()

    await group_cook()

    await http_wait_for()

    await task_semaphore()

    await cancel_task()

# ✅ 只在程序的最外层主入口调用一次 asyncio.run()
if __name__ == "__main__":
    asyncio.run(main())
```

# 完整示例 并发请求任务

```py
equest_semaphore = asyncio.Semaphore(5)
async def request_task(url: str) -> dict:
    async with request_semaphore:
        try:
            res = await client.get(url=url)
            # 非200的状态码，抛异常
            res.raise_for_status()
            logger.info(f"请求OK {url}")
            return {"url":url, "status":"OK", "text": res.text[:100]}
        except httpx.TimeoutException as e:
            logger.warning(f"请求超时 {url}")
            return {"url":url, "status":"timeout"}
        except httpx.HTTPStatusError as e:
            logger.warning(f"请求错误 {url}, code:{res.status_code}")
            return {"url":url, "satus":"http_error", "code":res.status_code}

async def request_group(urls:list) -> dict:
    results: dict = {} 
    # 异步上下文，使用 asyncio.TaskGroup() 来组织并发协程任务
    async with asyncio.TaskGroup() as tg:
        for url in urls:
            task = tg.create_task((request_task(url=url)))
            result = await task
            results[url] = result # 收集请求结果
    return results

# 调用：
urls: list = [
        url1,
        url2,
        url3
    ]
results = await request_group(urls=urls)
print(f"request_group: {results}")
```

# Anki 卡片

```py
Q: 想并发执行多个协程的两种写法？
A: 1) asyncio.TaskGroup (推荐, 3.11+); 2) asyncio.gather

Q: TaskGroup 比 gather 的核心优势？
A: 任一任务失败，自动取消其他任务；保证资源清理

Q: gather 结果是按什么顺序？
A: 按传入顺序，不是按完成顺序

Q: 「完成一个就处理一个」用什么？
A: asyncio.as_completed

Q: gather 想容忍部分失败用什么参数？
A: return_exceptions=True

Q: 协程里不小心写了 await some_coro() 没并发，问题在哪？
A: 直接 await 是顺序执行，要并发必须用 TaskGroup 或 gather 包装

Q: 协程里要跑同步阻塞代码怎么办？
A: await asyncio.to_thread(sync_func, *args)

Q: asyncio.run() 能调用几次？
A: 一次，且只能在最外层（不能在协程里调）

Q: 异步场景下 loguru 关键参数？
A: enqueue=True，避免日志写盘阻塞事件循环

Q: 取消协程任务后清理时，异常应该怎么处理？
A: 清理后重新 raise CancelledError，不要换异常类型
```