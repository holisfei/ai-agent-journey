# 类型注解

python类型注解不会在运行时进行类型检查，只是“提示”，不是“约束”

好处是可以用mypy做静态类型检查，好发现问题

## 基础数据类型

```python
# 字符
name: str = "str"
# 数字
age: int = 18
weight: float = 60.56
# bool
isLight: bool = False
# 空值，变量是str类型或者空值
empty: None | str = None
```

## 容器类型

```python
# 数组
numbers: list[int] = [1, 2, 3, 4]
# 字典
maps: dict[str, str] = {"name":"bob", "age":"18"}
# 集合
sets: set[str] = {"a", "b"}
# 定长元祖
tuples: tuple[int,float,int,int] = (1, 1.23, 3, 2)
# 不定长元祖
tuples2: tuple[int,...] = (1, 2, 3, 4, 5, 6)
```

## Optional 可选类型

Optional类似于swift当中可选类型，表示变量的值可以为空None

```python
timeout: Optional[float] = None
timeout = 1.12
```

## Union 联合类型

Union 表示变量的类型可以是多个类型

```python
user_id: Union[int, str, float] = 1
# 也可以这样表示类型 int | str | float
user_id1: int, str, float = 1
user_id = "one"
```

## Any 任意类型

Any 类似于 Swift当中的 any，表示变量的类型不做类型检查，运行时可以是任意类型

```python
value: Any = "done"
value = 1
```

## 泛型 python[T]

python泛型对应swift的泛型，有泛型约束的概念

```python
# 泛型可以直接用[T]来表示，对应swift的<T>
def get_first_item[T](data:list[T]) -> T:
    return data[0]

# 表示T只能为int或者float类型
def add[T: (int | float)](p1: T, p2: T) -> T:
    return p1 + p2
```

## 闭包

python中的闭包概念有
- 闭包函数的类型注解Callable
- 闭包函数
- lambda匿名闭包表达式

#### 闭包函数的类型注解Callable：表达了闭包函数的类型 

```Callable[[参数], 返回值]```

```python
# Callable[[int, str], bool] ->   对应swift的 (int, str) -> bool
# Callable[[], bool]         ->   对应swift的 () -> bool
# Callable[[int], bool]      ->   对应swift的 (int) -> bool
# Callable[[...], bool]      ->   任务参数
```

#### 闭包函数：对应swift的闭包函数，闭包捕获了外部的变量，闭包可以作为返回值和参数

```python
def make_counter(count: int) -> Callable[[], int]:
    number: int = 0
    def counter() -> int:
        nonlocal number # nonlocal表示捕获外部的变量，而不是新创建的变量
        number+=1
        return number
    return counter # 返回闭包函数的声明，并没有执行函数
counter = make_counter(count=1) # 返回闭包
res = counter() # 调用闭包
```

#### lambda匿名闭包：简短的闭包表达式，可以作为函数的参数

```python
# 常作为简短表达式
lamb = lambda x: x*2
print(f"Lambda：{lamb(2)}")
# Lambda作为参数
sort_res = sorted([3, 1, 4, 1, 5, 9, 2, 6], key=lambda x : -x) # 降序排列
print(f"Lambda排序：{sort_res}")
```

## 抽象类型：Sequence、Mapping、Iterable

函数参数如果是只读，可以用抽象类型来注解，使得函数更加灵活

```python
# list, tuple, set 都是序列 Sequence抽象类型
numbers: Sequence[float]
# dict 是映射 Mapping抽象类型
data: Mapping[str, int]
# 可以任意迭代的对象 Iterable类型，Sequence和Mapping都可以被迭代
items: Iterable[str]
```

## 例子

输入结构化字符串，输出dict

```python
def parse_configure(rawdata: str) -> dict[str, Union[str, int, bool]]:
    configure: dict[str, Union[str, int, bool]] = {}
    # 按行分割原始字符
    lines: list[str] = rawdata.splitlines()
    for line in lines:
        line = line.strip()
        if not line: # 跳过空行
            continue
        # 用 = 分割字符串
        key, _, value = line.partition("=")
        key: str = key.strip()
        value: str = value.strip()
        if value.isdigit():
            configure[key] = int(value)
        elif value.lower() in ("true", "false"):
            configure[key] = value.lower() == "true"
        else:
            configure[key] = value
    return configure


raw: str = """
host = localhost
port = 8080
debug = true
name = pythonLearning
"""
config = parse_configure(rawdata=raw)
print(f"结果：{config}")
```

## 使用mypy对文件做静态检查

```python
uv run mypy src/day2_typing.py # 单个文件检查
uv run mypy src/ # 目录下的文件检查
uv run mypy .    # 检查整个项目
```

## Anki 卡片

```python
Q: Python 中 Optional[T] 等价于什么？
A: T | None (3.10+)
   
Q: Python 泛型 3.12 新语法？
A: def func[T](items: list[T]) -> T:
   
Q: 闭包修改外部变量需要什么关键字？
A: nonlocal
   
Q: Callable 类型注解的格式？
A: Callable[[参数类型列表], 返回类型]
   
Q: 判断字符串是否全为数字？
A: s.isdigit()
```