
########## 迭代器 ########## 
from pathlib import Path
from re import X
import time


nums = [1, 2, 3]              # nums 是 Iterable
it = iter(nums)               # 用 iter() 从 Iterable 造出一个 Iterator
print(next(it))               # 1   ← next() 调用 it.__next__()
print(next(it))               # 2
print(next(it))               # 3
# print(next(it))               # StopIteration 异常 ← 取完了

it2 = iter(nums)
for i in it2: # 对一个迭代器可以迭代
    print(i)

########## 生成器 ########## 

# 生成器函数
# 调用函数时不执行而是返回了生成器对象，通过next()只执行一次下一个yield
def gen_numbers():
    print("start")
    yield 1
    print("middle")
    yield 2
    print("end")
    yield 3
gen = gen_numbers()
print(next(gen))
print(next(gen))

# 生成器的优势 - 节省内存
# 一次性生成100w数据，内存暴增
nums_list = [i for i in range(1_000_000)]
# 使用生成器函数，内存几乎为0
def nums_genfn(num: int):
    for i in range(num):
        yield i
# nums_genfn() 返回生成器，对生成器for in遍历会自动调用next()
for i in nums_genfn(num=1_000_000):
    if X > 1000:
        break

# 生成器的优势 - 流式处理
def streams_llm(text: str):
    for t in text:
        time.sleep(0.1) # 模拟 LLM api 返回数据
        yield t
for t in streams_llm(text="这里是python基础学习，正在进行流式输出!\n"):
    print(t, end="",flush=True) # flush-True保留之前的输出

# 生成器的优势 - 表达无限序列
def limit_no():
    n = 1
    while True:
        yield n
        n+=1
gen_limit = limit_no()
print(next(gen_limit))   # 1
print(next(gen_limit))   # 2
# 永远可以继续 next(),只要你不调就不算

########## 生成器表达式 ########## 

# 使用 () 来表示一个生成器对象
quares_gen = (i * i for i in range(10))
print(quares_gen)         # <generator object ...>
print(next(quares_gen))
print(list(quares_gen)) # 对生成器进行一次性迭代

########## yiels from ########## 
# yield from 将另外一个可迭代对象的所有值都yiels出去
def flatten(nested):
    """扁平化任意嵌套的列表"""
    for item in nested:
        if isinstance(item, list):
            yield from flatten(item)   # 递归扁平化子列表
        else:
            yield item

print(list(flatten([1, [2, [3, [4, 5]], 6], 7])))
# [1, 2, 3, 4, 5, 6, 7]

########## 惰性求值(Lazy Evaluation) ##########


########## itertools 惰性世界的工具箱 ##########

# chain 组合多个 可迭代对象
from itertools import chain
list1 = [1, 2, 3]
list2 = [4, 5]
list3 = [6]
print(list(chain(list1, list2, list3)))

# islice 给迭代器切片
from itertools import islice
def naturals():
    n = 1
    while True:
        yield n
        n+=1
# 取第 10 到 20 个
print(list(islice(naturals(), 10, 20)))
# 取前 5 个
print(list(islice(naturals(), 5)))

# takewhile / dropwhile —— 按条件截断
from itertools import takewhile, dropwhile
nums = [1, 2, 3, 8, 9, 1, 2]
# 只取条件满足的item
print(list(takewhile(lambda x: x < 5, nums)))   # [1, 2, 3]
# 丢弃条件满足的item，取剩下的item
print(list(dropwhile(lambda x: x < 5, nums)))   # [8, 9, 1, 2]

# groupby - 按照key进行分组，需要先按key排序
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

# batched —— 分批（Python 3.12+）
from itertools import batched
# 将list按照【每7个1组】为step进行分割
batch_generator = batched(list(range(99)), 7)
print(list(batch_generator))

# count / cycle / repeat —— 无限生成器
from itertools import count, cycle, repeat
# count 从某个数以step步长进行无限递增
for i, x in zip(count(start=100, step=10), ["a", "b", "c"]):
    print(i, x)# 100 a   110 b   120 c
# cycle：循环遍历
for item, color in zip(["A", "B", "C"], cycle(["red", "blue"])):
    print(item, color) # A red   B blue   C red
# repeat：重复值
list(repeat("x", 3))   # ['x', 'x', 'x']

# accumulate —— 累积计算
from itertools import accumulate
# 累加
acc_gen_add = accumulate([1,2,3,4], lambda a, b : a + b)
print(list(acc_gen_add))
# 累乘
acc_gen_mul = accumulate([1,2,3,4], lambda a, b : a * b)
print(list(acc_gen_mul))

# product / combinations / permutations —— 排列组合
from itertools import product, combinations
# 笛卡尔积（多重 for 循环的扁平版）
print(list(product([1, 2], ["a", "b"]))) # [(1, 'a'), (1, 'b'), (2, 'a'), (2, 'b')]
# 组合（不考虑顺序，两两组合）
print(list(combinations([1, 2, 3], 2))) # [(1, 2), (1, 3), (2, 3)]

# 示例，LLM 流水线
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