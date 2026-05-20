import asyncio
import time

import httpx
from loguru import logger


# 定义协程函数
async def boil_water():
    print("开始烧水")
    # await 模拟异步耗时操作
    # 事情循环机制会并发执行别的任务，不会卡在这里
    await asyncio.sleep(2.0)
    print("水烧开了")
    return "boil_water finished"


async def cut_vegetables():
    print("开始切菜")
    # await 模拟异步耗时操作
    await asyncio.sleep(1.0)
    print("菜切好了")
    return "cut_vegetables finished"


async def fail_task():  # 任务可能会失败
    await asyncio.sleep(1.0)
    # raise ValueError("fail_task 任务失败")


# asyncio.create_task 创建单个协程任务
async def cook():
    # 创建 协程任务 - asyncio.create_task
    task1 = asyncio.create_task(boil_water())
    task2 = asyncio.create_task(cut_vegetables())
    # 执行 协程任务
    result1 = await task1
    print(f"create_task 并发执行完成 结果 {result1}")

    result2 = await task2
    print(f"create_task 并发执行完成 结果 {result2}")


# asyncio.gather() 一次性并发执行任务 return_exceptions
async def gather_cook():
    # 直接把多个协程丢进 gather，它们会并发执行
    result = await asyncio.gather(
        boil_water(),
        cut_vegetables(),
        fail_task(),  # 任务失败，其余任务还在执行
        return_exceptions=True,  # 让失败的任务也返回异常结果，而不是不返回
    )
    # 携程函数返回的结果作为list返回  会严格按照传入 gather 的顺序
    print(f"gather_cook 并发执行完成结果 {result}")


# asyncio.as_completed 按顺序执行
async def completed_cook():
    for coro in asyncio.as_completed([boil_water(), cut_vegetables()]):
        result = await coro
        print(f"as_completed 并发执行完成结果 {result}")


# asyncio.TaskGroup 一个任务失败 所有任务取消，终结所有任务
async def group_cook():
    async with asyncio.TaskGroup() as tg:
        task1 = tg.create_task(cut_vegetables())
        task2 = tg.create_task(boil_water())
        task3 = tg.create_task(fail_task())  # 任务失败，取消所有

        result1 = await task1
        result2 = await task2
        result3 = await task3

        print(f"group_cook 结果{result1}")
        print(f"group_cook 结果{result2}")
        print(f"group_cook 结果{result3}")


# asyncio.wait_for 超时控制
async def timeout_process():
    print("开始加载")
    await asyncio.sleep(1.0)
    print("加载成功")


async def http_wait_for():
    try:
        result = await asyncio.wait_for(timeout_process(), timeout=2)
    except Exception as e:
        print(f"请求超时:{e}")


# asyncio.Semaphore 信号量 控制并发数
semaphore = asyncio.Semaphore(3)  # 同时只能执行3个任务


async def constrained_task(id: int):
    print("开始执行semaphore")
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
        constrained_task(id=5),
    )
    print(result)


# asyncio.to_thread() 线程池
def slow_sync_function(x: int) -> int:
    """假装这是个同步阻塞函数，不能改"""
    time.sleep(2)
    return x * 2


async def sync_to_thread():
    # ❌ 直接调用会阻塞事件循环
    # result = slow_sync_function(5)

    # ✅ 用 to_thread 扔到线程池跑，不阻塞事件循环
    result = await asyncio.to_thread(slow_sync_function, 5)
    print(f"to_thread()线程池 {result}")  # 10


# asyncio.CancelledError
async def long_task():
    try:
        print("long_task任务开始请求")
        await asyncio.sleep(6.0)
    except asyncio.CancelledError:
        print("long_task任务执行中断, 做其余清理/保存动作")
        raise  # 继续向上抛异常


async def cancel_task():
    task = asyncio.create_task(long_task())
    await asyncio.sleep(3)
    task.cancel()  # 取消任务
    try:
        await task
    except asyncio.CancelledError as v:
        print(f"cancel_task异常：{v}")


# httpx
# 公共header
headers = {"Content-Type": "application/json", "Accept": "application/json"}
# 连接10s超时，读取数据15s超时
timeout = httpx.Timeout(connect=10, read=15, write=30, pool=60)
# 最大连接数是100，其中保活连接最大20
limit = httpx.Limits(max_connections=100, max_keepalive_connections=20)
# 全局复用连接池，复用连接池，提高并发请求性能
# AsyncClient为异步client
client = httpx.AsyncClient(timeout=timeout, limits=limit, headers=headers)

base_url = "https://api.u-encry.com"
v2_info_exchange_rate = "/v2/info/exchange/rate"
v2_info_config_app = "/v2/info/config/app"
uc_v2_security_information = "/uc/v2/security/information"


# 普通请求
async def http_get_rate():
    res = await client.get(f"{base_url}{v2_info_exchange_rate}")
    print(res.json())


# streaming 流式请求
async def http_stream_rate():
    async with client.stream("GET", f"{base_url}{v2_info_exchange_rate}") as resp:
        async for chunk in resp.aiter_text():
            print(chunk, end="", flush=True)


# loguru日志库
def use_logger():
    # logger 基本使用
    # 日志配置 - 按照固定时间切割，只保留最近的
    # enqueue=True 开启异步写入日志
    logger.add(
        "logs/2026/app_{time}.log",
        rotation="00:00",
        retention="7 days",
        encoding="utf-8",
        enqueue=True,
    )
    # 日志配置 - 达到 100MB 就生成新文件，并自动压缩旧日志
    # logger.add(
    #    "logs/2026/app_{time}.log",
    #    retention="100 MB",
    #    compression="zip"
    # )
    logger.debug("这是一条调试信息")
    logger.info("程序正常运行中")
    logger.warning("需要注意的警告")
    logger.error("发生了错误")
    logger.success("操作成功完成！")  # Loguru 独有的 SUCCESS 级别


# logger 日志库异常捕获机制
def excep_capture():
    # 自动捕获异常
    @logger.catch
    def divid(x: int, y: int):
        x / y

    # 发生异常时，会自动捕获并记录完整的堆栈和变量值
    divid(x=1, y=0)
    # 手动捕获异常
    try:
        1 / 0
    except Exception:
        logger.exception("发生了一个除零异常")


# 示例
request_semaphore = asyncio.Semaphore(5)


async def request_task(url: str) -> dict:
    async with request_semaphore:
        try:
            res = await client.get(url=url)
            # 非200的状态码，抛异常
            res.raise_for_status()
            logger.info(f"请求OK {url}")
            return {"url": url, "status": "OK", "text": res.text[:100]}
        except httpx.TimeoutException:
            logger.warning(f"请求超时 {url}")
            return {"url": url, "status": "timeout"}
        except httpx.HTTPStatusError:
            logger.warning(f"请求错误 {url}, code:{res.status_code}")
            return {"url": url, "satus": "http_error", "code": res.status_code}


async def request_group(urls: list) -> dict:
    results: dict = {}
    # 异步上下文，使用 asyncio.TaskGroup() 来组织并发协程任务
    async with asyncio.TaskGroup() as tg:
        for url in urls:
            task = tg.create_task(request_task(url=url))
            result = await task
            results[url] = result  # 收集请求结果
    return results


# main 程序主入口，事件循环已经启动，对于协程任务只需要await就行
async def main():
    start = time.perf_counter()
    await cook()
    print(f"耗时{time.perf_counter() - start}s")

    start = time.perf_counter()
    await gather_cook()
    print(f"gather_cook耗时{time.perf_counter() - start}s")

    await completed_cook()

    await group_cook()

    await http_wait_for()

    await task_semaphore()

    # await slow_sync_function()

    await cancel_task()

    await http_get_rate()

    use_logger()

    urls: list = [
        f"{base_url}{v2_info_exchange_rate}",
        f"{base_url}{v2_info_config_app}",
        f"{base_url}{v2_info_config_app}",
    ]
    results = await request_group(urls=urls)
    print(f"request_group: {results}")

    # excep_capture()


# 只在程序的最外层主入口调用一次 asyncio.run()
if __name__ == "__main__":
    asyncio.run(main())
