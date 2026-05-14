from functools import wraps
import time

# 自定义装饰器

### 测量函数耗时装饰器
def timer(func):
    @wraps(func) # 保存函数签名信息
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        res = func(*args, **kwargs)
        end = time.perf_counter()
        duration = end - start
        print(f"函数{func.__name__} 耗时 {duration: .2f}s")
        return res
    return wrapper

@timer
def fetch_data():
    time.sleep(1)
    return "data"

fetch_data()

### 失败自动重试（带参数）装饰器
def retry(times: int = 3, delay: float = 1.0): # 1层：接收装饰器参数
    def decorator(func):                       # 2层：接收原函数
        @wraps(func)
        def wrapper(*args, **kwargs):          # 3层：接收原函数的参数
            last_exception = None
            for attempt in range(times):
                try: # 外部函数正常调用，不会再进行for循环，直接return
                    return func(*args, **kwargs)
                except Exception as e: # 外部函数抛出错误后，会进行for循环重试
                    last_exception = e
                    print(f"{e} 失败, 自动重试第{attempt+1}次")
                    if attempt < times - 1: # 不能超过最大重试次数
                        time.sleep(delay)   # 延时后进行重试
            # for 循环结束
            raise last_exception
        return wrapper
    return decorator

@retry(times=3, delay=1.0)
def call_api():
    """ 模拟可能失败的 API 调用 """
    import random
    if random.random() < 0.7: # 函数抛出错误，装饰器内部自动重试
        raise ConnectionError("call_api 失败 network error")
    return "call_api 成功"

res = call_api()
print(res)

# 系统装饰器

### @property
class Circle:
    def __init__(self, r: float):
        self.r = r
    
    @property
    def area(self) -> float:
        return 3.14 * self.r ** 2

c = Circle(5)
print(c.area) # 像访问属性一样，不用加 ()

### @classmethod @staticmethod
class User:
    count = 0
    
    @classmethod
    def get_count(cls) -> int:    # 接收类本身
        return cls.count
    
    @staticmethod
    def validate_email(email: str) -> bool:  # 不接收 self/cls
        return "@" in email

### @functools.lru_cache —— 自动缓存
from functools import lru_cache
from typing import Self

@lru_cache(maxsize=128)
def expensive_call(x: int) -> int:
    print(f"computing {x}")
    return x ** 2

expensive_call(5)   # computing 5
expensive_call(5)   # 不打印，直接返回缓存值

### @functools.cached_property —— 实例级缓存属性
from functools import cached_property
def expensive_parse(raw:str) -> str: # 解析逻辑
    return ""
class Document:
    def __init__(self, raw: str):
        self.raw = raw;

    @cached_property
    def parsed_content(self) -> dict:
        # 第一次访问时计算并缓存
        return expensive_parse(raw=self.raw)

### Pydantic 的 @field_validator、@model_validator