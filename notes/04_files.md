# 文件路径生成

```python
# 拼接出文件目录
DEMO_DIR = os.path.join(tempfile.gettempdir(), "com.python.learn", "04_files")
# 创建文件目录，如果目录存在则不创建
os.makedirs(DEMO_DIR, exist_ok=True)
# 根据前面生成的目录，生成具体的文件名
demo_file = os.path.join(DEMO_DIR, "test.txt") 
```

# 文件打开和关闭

```
# 打开
f = open(demo_file, "w", encoding="utf-8")
# 文件读取重置
f.seek(0)
# 关闭
f.close()
```

文件打开后每次都需要关闭，一个更便捷的方法是用with语句打开文件
```
with open(demo_file, "r", encoding="utf-8") as fi:
```
不关闭文件会导致：

- 文件描述符泄漏（File Descriptor Leak）：操作系统给每个进程的 fd 数量有限（通常 1024），泄漏多了会无法再打开新文件
- 数据丢失：写入的数据可能还在缓冲区，没真正落盘。崩溃或退出时数据丢失
- 文件被占用：Windows 上其他进程无法访问

### 文件打开时候的权限

```python
# 基础模式（必选其一）：
#   'r'  → 只读（默认）。文件不存在会报 FileNotFoundError
#   'w'  → 只写（覆盖）。文件不存在会创建，存在则清空
#   'a'  → 追加写入。文件不存在会创建，存在则在末尾追加
#   'x'  → 独占创建。文件已存在会报 FileExistsError
#
# 修饰模式（可组合）：
#   'b'  → 二进制模式（如 'rb'、'wb'）
#   't'  → 文本模式（默认，如 'rt' 等价于 'r'）
#   '+'  → 读写模式（如 'r+'、'w+'、'a+'）
```

# 文件读写

写入：
```python
with open(demo_file, "w", encoding="utf-8") as f:
    # 一次性写入全部内容
    f.write("hello python!\n")
    # 按行批量写入内容
    f.writelines(["hello oc!\n", "hello swift!\n", "hello flutter!\n"])
```
writelines 写入文件不会自动加换行，需要手动拼换行符

读取：
```python
f.read() # 一次性读取所有内容
f.read(2) # 只读取前2个字符
f.readline() # 读取一行
f.readline() # 在读取下一行
f.readlines() # 按行读取完所有文件，返回list
```

# python3 pathlib 新写法
```python
from pathlib import Path

# 路径拼接
demo_dir = Path(tempfile.gettempdir()) / "com.python.learn" / "04_files"
demo_dir.mkdir(parents=True, exist_ok=True)
demo_file = demo_dir / "test.txt"

demo_file.write_text("hello", encoding="utf-8")    # 一行写文件
content = demo_file.read_text(encoding="utf-8")    # 一行读文件
demo_file.exists()                                  # 文件是否存在
demo_file.suffix                                    # ".txt"
demo_file.stem                                      # "test"
demo_file.parent                                    # 父目录
list(demo_dir.glob("*.txt"))                       # 列出所有 .txt 文件
```