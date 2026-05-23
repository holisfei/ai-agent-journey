# 装饰器

```from functools import wraps```

装饰器的本质是接收函数，再返回新函数。其核心作用是处理公共的逻辑。

是语法糖，是@```@my_decorator```的语法属性，等价于```foo = my_decorator(foo)```

```python
@my_decorator
def foo():
    pass

# 等价于
def foo():
    pass
foo = my_decorator(foo)   # ← 这才是装饰器的本质
```

在接收函数后，装饰器内部保存了原函数的签名信息，又重新定义了装饰器函数，在装饰器函数内部调用了接受的原函数，然后返回这个装饰器函数。在返回之前可以做一些前置和后置的逻辑，比如计时、日志等。

装饰器内部为什么要保留原函数签名：装饰器内部包住原函数，如果不保留原函数的签名信息，那原函数的一些签名信息(```__name__, __qualname__, __doc__, __dict__, __module__,__wrapped__```)就会丢失。

通过```@wraps(func)```来实现原函数的信息保留(```from functools import wraps```)，可以通过原函数.```__wrapped__```来获取原函数本身

装饰器也可以接受额外的参数，这大大提高了装饰器内部函数逻辑的灵活性。

装饰器有两类：函数装饰器和类装饰器
- 函数装饰器顾名思义就是函数，本身就是闭包的返回和调用
- 类装饰器可以有属性和状态，可以暴露出方法，可被继承

装饰器既可以用在函数，也可以用在类

所以，装饰器的本质核心逻辑就是：
- 定义装饰器(函数/类)
- 接收外部传入的函数/类
- 定义内部装饰器函数，接收外部函数的参数
    - 内部装饰器逻辑处理，一般是公共的逻辑
- 返回经过装饰的函数/类

# 函数装饰器

函数装饰器一般用于，在处理公共逻辑的时候不需要状态存储、额外属性存储的场景

### 装饰器无参数

基本模版：

```python
# 定义函数装饰器
def wrapperfn(func):               # 接收外部函数
    @wraps(func)                   # 保留外部函数的签名信息
    def wrapper(*args, **kwargs):  # 接受函数参数
                                   # 前置逻辑
        res = func(*args, **kwargs)# 调用外部函数
                                   # 后置逻辑
        return res                 # 返回值

    return wrapper                 # 返回装饰器新函数

# 使用函数装饰器
@wrapperfn
def usefn(a: int, b: int):
    return a + b
```

示例：统计耗时的 函数装饰器

```python
def timer(func):
    """统计耗时函数的装饰器"""
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
```

使用```@xxx```来使用定义好的函数装饰器，本质就是将这个函数作为参数传入到装饰器

### 装饰器带参数

基本模版：

```python
# 定义函数装饰器
def parafn(extra: int):                # 接收装饰器参数
    def wrapperfn(func):               # 接收外部函数
        @wraps(func)                   # 保留外部函数的签名信息
        def wrapper(*args, **kwargs):  # 接受函数参数
                                       # 前置逻辑
           res = func(*args, **kwargs) # 调用外部函数
                                       # 后置逻辑
           return res                  # 返回值
        return wrapper                 # 返回装饰器新函数
    return wrapperfn                   # 返回新函数

# 使用函数装饰器
@parafn(extra = 1)
def usefn(a: int, b: int):
    return a + b

# 调用函数
usefn(a=1, b=1)
```

### 示例：失败自动重试的 带参数函数装饰器

```python
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
```

# 类装饰器

类数装饰器本质是类，一般用于，在处理公共逻辑的时候需要状态存储、额外属性存储的场景

类作为装饰器使用，需要实现```__call__```方法，需要在```__init__```接受参数

### 类装饰器无参数

基本模版：

```python
# 定义
class para0Cls:
                                            # 可以有额外的类属性
    def __init__(self, func):               # 接受 外部函数
        wraps(func)(self)                   # 保留外部函数签名信息
        self.func = func                    # 保存 外部函数
                                            # 可以有额外的实例属性
    def __call__(self, *args, **kwargs):    # 装饰器函数：接受 外部函数的参数
                                        # 前置逻辑
        res = self.func(*args, **kwargs)# 调用外部函数
                                        # 后置逻辑     
        return res                      # 返回值

# 使用
@para0Cls
def compute(n):
    return sum(range(n + 1))

# 调用函数
compute(n=10)
```

可以看到无参类装饰器本质就是，用``` __init__``` 和 ```__call__``` 来分别接受外部函数和外部函数参数

### 类装饰器带参数

基本模版：

```python
# 定义
class para1Cls:
                                            # 可以有额外的类属性
    __init__(self, expara: int):            # 接受 装饰器 参数
        self.expara = expara                # 保存 参数
                                            # 可以有额外的实例属性
    __call__(self, func):                   # 接受 外部函数
        @wraps(func)                        # 保留外部函数签名信息
        def wrapper(*args, **kwargs): # 装饰器函数：接受 外部函数的参数
                                            # 前置逻辑
            res = func(*args, **kwargs)     # 调用外部函数
                                            # 后置逻辑     
            return res                      # 返回值
        return wrapper                      # 返回装饰器函数

# 使用
@para1Cls(expara=1)
def compute(n):
    return sum(range(n + 1))

# 调用函数
compute(n=10)
```

可以看到带参数的类装饰器，是在```__init```中接受额外的参数，在```__call```接受函数外部函数，定义和返回的新的装饰器函数

# 装饰器修饰类

以上我们看到的是使用装饰器修饰了函数
- 装饰器接收的是函数
- 保存外部函数的签名信息
- 调用外部函数
- 返回的是经过装饰的新函数

装饰器也可以修饰类
- 装饰器接收的是类对象，非实例
- 保存了外部类的元信息
- 调用类的初始化方法
- 返回的是经过装饰的原类对象

### 函数装饰器修饰类

基本模版：

```python
# 定义函数装饰器：
def auto_repr(cls):                         # 接受类
    """给类自动生成 __repr__"""
    original_init = cls.__init__            # 保存类的初始化函数

    @wraps(original_init)                   # 保存类的元信息
    def wrapper(self, *args, **kwargs):
        original_init(self, *args, **kwargs)# 调用类的初始化

    def __repr__(self):
        attrs = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"{cls.__name__}({attrs})"

    cls.__repr__ = __repr__                 # 给类生成 __repr__ 属性
    return cls                              # 返回的是类

# 使用：
@auto_repr
class User:
    def __init__(self, name, age):
        self.name = name
        self.age = age

```

### 类装饰器修饰类

基本模版：

```python
# 定义类装饰器：
class PluginRegistry:
    """插件注册中心"""

    def __init__(self):                    
        self._plugins = {}

    # 自定义的装饰器函数，不是系统的 __call__,
    # 本质其实就是一个带参数的类装饰器
    def register(self, name=None):        # 接收装饰器参数 类名称
        """注册插件（装饰器）"""
        def decorator(cls):               # 定义装饰器函数 接受类
            plugin_name = name or cls.__name__
            self._plugins[plugin_name] = cls
            return cls                    # 返回 类
        return decorator                  # 返回 装饰器函数

    def get(self, name):
        return self._plugins.get(name)

    def list_plugins(self):
        return list(self._plugins.keys())

# 使用装饰器
registry = PluginRegistry() # 初始化装饰器

@registry.register("json_parser")
class JSONParser:
    def parse(self, data): return f"JSON: {data}"

@registry.register("xml_parser")
class XMLParser:
    def parse(self, data): return f"XML: {data}"

@registry.register()
class YAMLParser:
    def parse(self, data): return f"YAML: {data}"

```

我们看到，这里使用了类装饰器去修饰了一个类，类装饰器内部自定义了装饰器函数，代替了原有的```__call__```函数，其实本质和原理都是一致的
- 接收装饰器的参数
- 接收类/函数
- 调用类/函数(前后逻辑处理)
- 返回经过装饰的类/函数

# 系统内置装饰器

### @property —— 计算属性

```python
class Circle:
    def __init__(self, r: float):
        self.r = r
    
    @property
    def area(self) -> float:
        return 3.14 * self.r ** 2

c = Circle(5)
print(c.area)   # 像访问属性一样，不用加 ()
```

### @classmethod - 类方法    @staticmethod - 静态方法

```python
class User:
    count = 0

    @classmethod # 只接收类本身
    def get_count(cls) -> int:
        return cls.count

    @staticmethod # 不接收 self/cls
    def validate_email(email: str) -> bool:
        return "@" in email
```

- 如果方法里需要用到 ```self.xxx```（实例的数据）：那就写成普通的实例方法。
- 如果方法里需要用到 ```cls.xxx``` 或 ```类名.xxx```（类的共享数据），或者需要返回一个类的实例：那就用 ```@classmethod```。
- 如果方法里既不需要 ```self``` 也不需要 ```cls```，只是恰好跟这个类有点关系，想把它塞进类里统一管理：那就用 ```@staticmethod```。

### @functools.lru_cache —— 自动缓存

```@lru_cache``` 是给“纯函数”用的

采用 LRU（Least Recently Used）算法。它会把函数的参数作为键（Key），返回值作为值（Value）存起来。下次用同样的参数调用时，直接返回缓存的结果。

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_call(x: int) -> int:
    print(f"computing {x}")
    return x**2


expensive_call(5)  # computing 5
expensive_call(5)  # 不打印，直接返回缓存值
```

### @functools.cached_property —— 实例级缓存属性

```@cached_property``` 是给“对象（实例）”用的

它把一个方法伪装成一个属性，并且只在第一次访问时计算，之后就把结果存在该实例的内存里。

```python
from functools import cached_property

def expensive_parse(raw: str) -> str:  # 解析耗时逻辑
    return ""

class Document:
    def __init__(self, raw: str):
        self.raw = raw # 假设这是很庞大的原始数据

    @cached_property # 用于对象实例
    def parsed_content(self) -> dict:
        # 第一次访问时计算并缓存
        return expensive_parse(raw=self.raw)

doc = Document("非常庞大的数据")
print(doc.parsed_content)  # 第一次访问：打印提示并等待1秒，输出计算结果
print(doc.parsed_content)  # 第二次访问：瞬间输出结果（直接从实例内存读取，不再计算）
```

### Pydantic 的 @field_validator、@model_validator

# Anki 卡片

```python
Q: @decorator 语法糖等价于什么？
A: foo = decorator(foo)

Q: @decorator(arg) 语法糖等价于什么？
A: foo = decorator(arg)(foo)

Q: 装饰器内部保留原函数元信息的方法？
A: from functools import wraps; @wraps(func)

Q: 带参数装饰器需要几层嵌套？
A: 3 层（参数 → func → wrapper）

Q: wrapper 内部调用原函数时容易忘记什么？
A: return

Q: 类装饰器需要实现哪两个方法？
A: __init__ 接收 func，__call__ 接收调用参数

Q: 自动缓存函数返回值的标准库装饰器？
A: @functools.lru_cache(maxsize=N)
```