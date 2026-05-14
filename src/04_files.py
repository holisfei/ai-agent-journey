import os
import tempfile

# 文件路径的生成
DEMO_DIR = os.path.join(tempfile.gettempdir(), "com.python.learn", "04_files") # 拼接出文件目录
os.makedirs(DEMO_DIR, exist_ok=True) # 创建文件目录，如果目录存在则不创建
demo_file = os.path.join(DEMO_DIR, "test.txt") # 根据前面生成的目录，在目录下创建文件
print(f"路径：{DEMO_DIR}")

# 文件写入
# 文件打开权限
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
f = open(demo_file, "w", encoding="utf-8") # 打开文件，权限写
f.write("hello python!\n") # 一次性写入全部内容
f.writelines(["hello oc!\n", "hello swift!\n", "hello flutter!\n"]) # 按行批量写入
f.close() # 写完后关闭文件

# 文件读取
f = open(demo_file, "r", encoding="utf-8") # 打开文件，权限度
c_t = f.read() # 一次行读取所有内容
print(f"{c_t}")

f.seek(0) # 从开头开始读取，要不然会记录上次的读取位置
c_h = f.read(2) # 只读取前2个字符
print(f"{c_h}")

f.seek(0) # 
c_1 = f.readline() # 读取一行
c_2 = f.readline() # 在读取下一行
print(f"{c_1}")
print(f"{c_2}")

f.seek(0) # 
c_s = f.readlines() # 按行读取完所有文件，返回list
print(f"{c_s}")

f.close()

# 使用 with 语句 进行 便捷读写
# with语句 自动处理了文件的 close
with open(demo_file, "r", encoding="utf-8") as fi:
    print(f"{fi.read()}")
    fi.seek(0)
    print(f"{fi.readline()}")
    print(f"{fi.readline()}")

#  python3 pathlib 新写法
from pathlib import Path
path_dir = Path(tempfile.gettempdir()) / "com.python.learn" / "04_files"
path_dir.mkdir(parents=True, exist_ok=True)
demo_file = path_dir / "demo.txt"
print(f"新路径：{demo_file}")

demo_file.write_text("hello pathlib", encoding="utf-8")     # 一行写文件
content = demo_file.read_text(encoding="utf-8")     # 一行读文件
print(f"{content}")
demo_file.exists()                                  # 文件是否存在
demo_file.suffix                                    # ".txt"
demo_file.stem                                      # "demo"
demo_file.parent                                    # 父目录
list(path_dir.glob("*.txt"))                        # 列出所有 .txt 文件