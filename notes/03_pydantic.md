# 1. Pydantic 是什么、解决什么问题

核心价值：解析 + 验证 + 转换 + Schema 生成

pydantic 是数据验证的核心库，输入的数据具有不确定性，比如前端传入的字段、爬取的一段字段，pydantic需要保证数据在系统边界上能保证符合预期

pydantic 是应用的「数据边界守门员」。来自外部世界（用户、LLM、API、文件）的所有数据必须先过这道关，才能被代码信任。

# 2. 定义 Model
- 字段类型注解
- Field() 字段的内置约束（min_length、gt、pattern...）
- 默认值与可选字段 None | str 
- 嵌套 Model

# 3. 数据进入：四种构造方式
- 直接调用 User(name="", age=1, ...)
- **kwargs 展开 User(**data), 可以将 dict 自动转成 key=value的形式
- Model类型.model_validate(dict) -> model实例
    - dict 转 model
- Model类型.model_validate_json(str) -> model实例
    - json str 转 model

# 4. 数据出去：序列化
- model实例.model_dump() -> dict
    - model实例 转 json
- model实例.model_dump_json() -> str
    - model实例 转 json str
- 控制：exclude, include, by_alias

# 5. 自定义验证
- @field_validator
    - 单字段，需要返回值
- @model_validator(mode="after")
    - 多字段，需要返回值, after 所有字段都拿到且验证后之后再进行
- 验证器的返回值是新值

# 6. Model配置：ConfigDict
- extra='forbid'（推荐开）
    - 配置接收额外字段
- strict=True（谨慎开）
    - 配置是否自动类型转化
- frozen=True（不可变）
    - 配置是否实例化后可改变属性

# 7. 高级特性
- 计算字段 @computed_field @property
    - 计算字段实例化不需要传入，转出的时候会带着
- 字段别名 alias
    - 传入的时候字段字段名称不匹配的时候用
- JSON Schema 生成（→ Function Calling）

# 例子
```python
from pydantic import (
    BaseModel, 
    ConfigDict, 
    Field, 
    EmailStr,
    computed_field, 
    field_validator, 
    model_validator
)

class UserInput(BaseModel):
    """模拟用户的登录字段"""

    # 长度最小是2，最大是10,
    # alias 字段别名，和外部字段名称不一致时候
    name: str = Field(min_length=3,max_length=10,alias="nick")
    # 需要添加依赖 uv add 'pydantic[email]'
    email: EmailStr
    # 可选，默认 None
    invite_code: str | None = None
    # default默认值 gt 必须大于0
    # 即使用户传入的是 str 类型，通过model后会得到int类型的数据（前提配置strict=False）
    age: int = Field(default=18,gt=0)
    pwd: str 
    confirm_pwd: str

    # model_config 配置：
    # strict=True，关闭自动类型转换，传啥类型就是啥类型
    # extra='forbid', 传入未定义的字段会报错, ignore-忽略，allow-允许
    # frozen=True, 模型创建实例化后，不可以修改属性值
    # populate_by_name=True, 按照别名取值
    model_config = ConfigDict(strict=False, extra="allow", frozen=True, populate_by_name=True)

    # @field_validator 单字段数据验证
    @field_validator("name")
    @classmethod # 显示标注是个 class method
    def validate_name(cls, v: str) -> str: # 加类型注解
        forbidden = set("*&^%$#@!")
        if any(c in forbidden for c in v) :
            # ValidationError 比 Exception 更精确
            raise ValidationError("name 不能包含特殊字符")
        return v

    # @model_validator 多字段数据验证
    # after表示当所有单字段验证通过后，再进行验证
    @model_validator(mode="after")
    def validate_pwd_match(self): # self表示拿到当前model
        if self.pwd != self.confirm_pwd:
            raise ValidationError("两次密码不一致")
        if len(self.pwd) < 6:
            raise ValidationError("密码必须大于6位")
        return self

    # 计算字段 (Computed Field)
    # 在 model_dump_json 转化为json str 的时候会被带着
    @computed_field
    @property
    def nick_name(self) -> str:
        return f"{self.name}_{self.age}"


# 调用
try:
    # 方式1：直接传参
    # input = UserInput(name="holis", email="holis@gmail.com", age=35, pwd="123456", confirm_pwd="123456")
    
    # 方式2：json 传参，然后 ** 解包
    form_data:dict[str,str|int] = {
        "name":"holis", 
        "email":"holis@gmail.com",
        "age":35, 
        "pwd":"123456", 
        "confirm_pwd":"123456" 
    }
    # ** 将json自动展开成 key=value 的形式
    user_input = UserInput(**form_data)
    print(f"age: {user_input.age}")

except Exception as e:
    print(f"验证失败：{e}")

# 数据传入和传出：json 和 model互转
try:
    # model 转 json str： model_dump_json
    user_json = user_input.model_dump_json()
    print(f"转json {user_json}");

    # model 转 json：model_json_schema()
    json = UserInput.model_json_schema()

    # json 转 model
    # model_validate_json：接收 json str
    # model_validate：接受 json
    user_model = UserInput.model_validate(form_data)
    print(f"转model {user_model.name}")
except Exception as e:
    print(f"转化失败：{e}")
```

## Anki 卡片
```python
Q: Pydantic 把 model 转成 dict？
A: model_dump()

Q: Pydantic 把 model 转成 JSON 字符串？
A: model_dump_json()

Q: Pydantic 从 dict 验证生成 model？
A: ClassName.model_validate(d)

Q: Pydantic 从 JSON 字符串验证生成 model？
A: ClassName.model_validate_json(s)

Q: ConfigDict 中禁止额外字段的配置？
A: extra='forbid'

Q: 单字段验证装饰器？
A: @field_validator("字段名")

Q: 多字段验证装饰器？
A: @model_validator(mode="after")
```