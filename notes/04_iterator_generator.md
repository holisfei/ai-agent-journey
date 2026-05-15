# 迭代器 Iterator

python的for循环，底层做了两件事情：
- 1. 找到这个容器的「取下一个」操作 ```Iteraor```
- 2. 反复调用它 ```next()```，直到没东西可取

python对于容器类型的数据，是可以迭代的，可以迭代的对象是 Iterable，其本质是实现了```__iter__```方法的对象

对于一个```Iterable```对象调用```iter()```就可以拿到其迭代器```Iterator```，迭代器做的事情就实现了```__next__```方法

对一个```Iterator```一直调用```next()```方法，直道迭代器被迭代完抛出异常```StopIteration```

一个 ```Iterator``` 走完就废了，要再来一次得新建```Iterator```

```python
nums = [1, 2, 3]              # nums 是 Iterable
it = iter(nums)               # 用 iter() 从 Iterable 造出一个 Iterator
print(next(it))               # 1   ← next() 调用 it.__next__()
print(next(it))               # 2
print(next(it))               # 3
print(next(it))               # StopIteration 异常 ← 取完了

it2 = iter(nums)
for i in it2: # 对一个迭代器可以迭代
    print(i)
```

# 生成器 Generator

生成器是特殊的 Iterator，是一种用「函数语法」创建出来的 Iterator，最大特点是「需要时才计算」。

### 生成器函数 和 普通函数

普通函数一次性返回所有计算结果，生成器函数不会一次性返回所有计算结果，而是按需要返回计算结果
```python
def get_numbers():
    print("computing...")
    return [1, 2, 3, 4, 5]     # 一次性算完返回

nums = get_numbers()  # 立刻打印 "computing..."
print(nums)           # [1, 2, 3, 4, 5]
```

生成器函数：函数体里有 yield，调用时不执行任何代码，只返回一个生成器对象。每次 next() 才执行到下一个 yield。
```python
def get_numbers():
    print("start")
    yield 1
    print("middle")
    yield 2
    print("end")
    yield 3

gen = get_numbers()    # ← 什么都没打印，函数体没执行！
print(next(gen))       # start  →  1   (执行到第一个 yield 暂停)
print(next(gen))       # middle →  2   (从暂停处恢复，到下一个 yield)
print(next(gen))       # end    →  3
print(next(gen))       # StopIteration 异常
```

yield: 函数执行到yield，先暂停(保留执行位置和所有局部变量)，下次next()，在继续从保留的位置执行，直到遇到下一个yield或者函数结束

### 为什么要【按需】

#### 1. 节省内存
```python
# 普通写法：把 1 亿个数全装进内存
nums = [i * i for i in range(100_000_000)]   # 💥 几个 GB

# 生成器写法：用一个算一个，内存几乎为零
def squares(n):
    for i in range(n):
        yield i * i

for x in squares(100_000_000):    # ✅ 内存几乎不增长
    if x > 100:
        break
    print(x)
```
#### 2. 可进行流式处理
```python
def stream_llm_response(prompt: str):
    # 假装这是真实的 LLM API
    for chunk in api.stream(prompt):
        yield chunk.text             # 收到一段就吐一段

# 调用方边收边显示
for chunk in stream_llm_response("讲个笑话"):
    print(chunk, end="", flush=True)   # 像 ChatGPT 那样逐字显示
```
#### 3. 可以表达无限序列
```python
def naturals():
    n = 1
    while True:        # 无限循环
        yield n
        n += 1

gen = naturals()
print(next(gen))   # 1
print(next(gen))   # 2
# 永远可以继续 next(),只要你不调就不算
```

生成器其实就是 Iterator, 任何能用 Iterator 的地方，都能用生成器。所以 Python 大量内置函数（map、filter、zip）返回的都是生成器/迭代器，不会立刻物化成 list，对他们(生成器)迭代的时候才会进行进行list化

# 生成器表达式

生成器函数太啰嗦了，需要def函数+yield 才能表达完整的生成器
，Python 给了一个单行写法——把列表推导式的 [] 换成 ()：
```python
# 列表推导式：立刻计算所有，返回 list
squares_list = [i * i for i in range(10)]
print(squares_list)        # [0, 1, 4, 9, ..., 81] ← 真实的 list

# 生成器表达式：返回一个生成器对象，按需计算
squares_gen = (i * i for i in range(10))
print(squares_gen)         # <generator object ...>
print(next(squares_gen))
print(list(squares_gen))   # [0, 1, 4, 9, ..., 81] ← 这一刻才计算
```
使用选择：
```python
# ✅ 用列表推导式：需要反复用，或要索引
results = [process(x) for x in data]
print(results[0])
print(len(results))

# ✅ 用生成器表达式：只遍历一次，或处理大数据
total = sum(x * x for x in range(1_000_000))   # 边算边加，内存几乎为零
```

# yield from

yield from 简单说：「把另一个可迭代对象的所有值都 yield 出去」。
, 拆分大生成器、扁平化嵌套结构、组合多个生成器。

```python
def flatten(nested):
    """扁平化任意嵌套的列表"""
    for item in nested:
        if isinstance(item, list):
            yield from flatten(item)   # 递归扁平化子列表
        else:
            yield item

print(list(flatten([1, [2, [3, [4, 5]], 6], 7])))
# [1, 2, 3, 4, 5, 6, 7]
```

# 惰性求值(Lazy Evaluation)

惰性求值：「需要的时候才算」，而不是「一次性全算完」。

惰性求值的好处不只是省内存，惰性的真正威力是短路计算——可以「在合适时机停下来」

这就是为什么 Python 圈推崇生成器——不只是省内存，更是让你的代码有机会提前结束。

LLM 应用里这个理念无处不在：流式 token 一边收一边显示，用户随时可以打断；分块处理大文件，处理到目标就停。

# itertools 惰性世界的工具箱

itertools 它是一组返回迭代器的工具函数，专门用来组合、变换、过滤迭代器，全都是惰性的。

### 1. chain —— 把多个 iterable 接起来
```python
from itertools import chain

list1 = [1, 2, 3]
list2 = [4, 5]
list3 = [6]

print(list(chain(list1, list2, list3)))
# [1, 2, 3, 4, 5, 6]
```

### 2. islice —— 给迭代器切片
```python
from itertools import islice

def naturals():
    n = 1
    while True:
        yield n
        n += 1

# 取第 10 到 20 个
print(list(islice(naturals(), 10, 20)))
# [11, 12, ..., 20]

# 取前 5 个
print(list(islice(naturals(), 5)))
# [1, 2, 3, 4, 5]

```

### 3. takewhile / dropwhile —— 按条件截断
```python
rom itertools import takewhile, dropwhile
nums = [1, 2, 3, 8, 9, 1, 2]
# 只取条件满足的item
print(list(takewhile(lambda x: x < 5, nums)))   # [1, 2, 3]
# 丢弃条件满足的item，取剩下的item
print(list(dropwhile(lambda x: x < 5, nums)))   # [8, 9, 1, 2]
```

### 4. groupby —— 按 key 分组（注意：要先排序）
```python
from itertools import groupby
logs = [
    {"level": "INFO", "msg": "a"},
    {"level": "INFO", "msg": "b"},
    {"level": "ERROR", "msg": "c"},
    {"level": "INFO", "msg": "d"},
]
# 必须先按 key 排序！groupby 只能合并相邻同 key 的项
logs.sort(key=lambda x: x["level"])
logs_generator = groupby(logs, key=lambda x: x["level"])
for key,loglist in logs_generator:
    print(f"{key}: {list(loglist)}")
# ERROR: [{'level': 'ERROR', 'msg': 'c'}]
# INFO: [{'level': 'INFO', 'msg': 'a'}, {'level': 'INFO', 'msg': 'b'}, {'level': 'INFO', 'msg': 'd'}]
```

### 5. batched —— 分批（Python 3.12+）
```python
from itertools import batched
# 将list按照【每7个1组】为step进行分割
batch_generator = batched(list(range(99)), 7)
print(list(batch_generator))
```

### count / cycle / repeat —— 无限生成器
```python
from itertools import count, cycle, repeat

# count：从某个数无限递增
for i, x in zip(count(start=100, step=10), ["a", "b", "c"]):
    print(i, x)
# 100 a   110 b   120 c

# cycle：循环遍历
for item, color in zip(["A", "B", "C"], cycle(["red", "blue"])):
    print(item, color)
# A red   B blue   C red

# repeat：重复值
list(repeat("x", 3))   # ['x', 'x', 'x']
```

### 7. accumulate —— 累积计算
```python
from itertools import accumulate
# 累加
acc_gen_add = accumulate([1,2,3,4], lambda a, b : a + b)
print(list(acc_gen_add)) # [1, 3, 6, 10]
# 累乘
acc_gen_mul = accumulate([1,2,3,4], lambda a, b : a * b)
print(list(acc_gen_mul)) # [1, 2, 6, 24]
```

### 8. product / combinations / permutations —— 排列组合
```python
rom itertools import product, combinations
# 笛卡尔积（多重 for 循环的扁平版）
print(list(product([1, 2], ["a", "b"]))) # [(1, 'a'), (1, 'b'), (2, 'a'), (2, 'b')]
# 组合（不考虑顺序，两两组合）
print(list(combinations([1, 2, 3], 2))) # [(1, 2), (1, 3), (2, 3)]
```

# 迭代器和生成器全景

```python
┌────────────────── 协议层（最底层概念） ──────────────────┐
│                                                       │
│   Iterable      ←─── 实现 __iter__，能被 for 遍历        │
│       │                                                │
│       ├─→ iter(obj) ─→  Iterator   ←─ 实现 __next__     │
│                              │                         │
│                              └─→  next(it) 取下一个      │
│                                                         │
└────────────────────────────────────────────────────────-┘
                          ↑
                          │ 一种特殊的 Iterator
                          │
┌────────── 生成器层（创建 Iterator 的便捷方式） ──────────┐
│                                                      │
│   ① 生成器函数        def f(): yield x                │
│   ② 生成器表达式      (x for x in ...)                 │
│   ③ yield from        把子生成器的值都吐出来             │
│                                                       │
└───────────────────────────────────────────────────────┘
                          ↑
                          │ 体现了
                          │
┌─────────────────── 设计哲学层 ───────────────────────────┐
│                                                        │
│   惰性求值：用到才算，可提前停止                            │
│   优点：省内存 / 流式处理 / 短路 / 支持无限序列              │
│                                                        │
└────────────────────────────────────────────────────────┘
                          ↑
                          │ 工具集
                          │
┌──────────────────── 工具层 ──────────────────────────────┐
│                                                         │
│   itertools: chain / islice / batched / groupby ...     │
│   都返回 Iterator，可链式组合，全程惰性                      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

# 综合示例
```python
def read_line(path: Path):
    """生成器函数：读取单个文件内容"""
    with open(path, encoding="utf-8") as f:
        for line in f: # 读取文件内容，yield 惰性读取
            yield line.strip()

def read_paths(paths:list[Path]):
    """生成器函数：读取多个文件内容"""
    for path in paths:
        yield from read_line(path=path) # yield from 连接多个文件

def clear_content(lines):
    """生成器函数：数据清洗，去除空行+转小写"""
    return (line.lower() for line in lines if line)

def pippeline(files: list[Path], max_lines: int = 1000, batch_size: int = 10):
    # 1. 多文件处理 得到生成器，得到需要待处理的文字行
    all_lines = read_paths(paths=files)

    # 2. 数据清洗，得到生成器
    clearned = clear_content(lines=all_lines)

    # 3. 分片数据，最多处理 1000 行数据
    limited = islice(clearned, max_lines)

    # 4. 分批数据，按照 10 个一组进行分割，得到list
    for batch in batched(limited, batch_size):
        # 假装这里调 LLM API 做批量处理
        print(f"Processing batch of {len(batch)} lines")
        yield batch

# 使用：
files = [Path("a.txt"), Path("b.txt"), Path("c.txt")]
for batch in pippeline(files, max_lines=100, batch_size=10):
    # 一边处理一边消费，内存几乎不增长
    pass
```

# Anki 卡片
```
Q: Iterable 和 Iterator 的关系？
A: Iterable 实现 __iter__，能产生 Iterator；Iterator 实现 __next__，真正干「取下一个」的活

Q: 生成器是什么？
A: 用 yield 语法或生成器表达式创建的一种 Iterator，惰性求值

Q: yield 的核心语义？
A: 暂停函数并返回一个值，下次 next() 从这里恢复

Q: 列表推导式 vs 生成器表达式？
A: [...] 立即算完返回 list；(...) 按需算返回 generator

Q: yield from 的作用？
A: 把另一个 iterable 的所有值依次 yield 出去（委托）

Q: 生成器能遍历几次？
A: 一次。耗尽后要重新创建

Q: 把大数据分批处理用 itertools 哪个工具？
A: batched(data, n) (Python 3.12+)

Q: 取生成器前 N 个元素？
A: itertools.islice(gen, N)
```