from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    ValidationError,
    computed_field,
    field_validator,
    model_validator,
)


class UserInput(BaseModel):
    """模拟用户的登录字段"""

    # 长度最小是2，最大是10,
    # alias 字段别名，和外部字段名称不一致时候
    name: str = Field(min_length=3, max_length=10, alias="nick")
    # 需要添加依赖 uv add 'pydantic[email]'
    email: EmailStr
    # 可选，默认 None
    invite_code: str | None = None
    # default默认值 gt 必须大于0
    # 即使用户传入的是 str 类型，通过model后会得到int类型的数据（前提配置strict=False）
    age: int = Field(default=18, gt=0)
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
    @classmethod  # 显示标注是个 class method
    def validate_name(cls, v: str) -> str:  # 加类型注解
        forbidden = set("*&^%$#@!")
        if any(c in forbidden for c in v):
            # ValidationError 比 Exception 更精确
            raise ValidationError("name 不能包含特殊字符")
        return v

    # @model_validator 多字段数据验证
    # after表示当所有单字段验证通过后，再进行验证
    @model_validator(mode="after")
    def validate_pwd_match(self):  # self表示拿到当前model
        if self.pwd != self.confirm_pwd:
            raise ValidationError("两次密码不一致")
        if len(self.pwd) < 6:
            raise ValueError("密码必须大于6位")
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
    form_data: dict[str, str | int] = {
        "name": "holis",
        "email": "holis@gmail.com",
        "age": 35,
        "pwd": "123456",
        "confirm_pwd": "123456",
    }
    # ** 将json自动展开成 key=value 的形式
    user_input = UserInput(**form_data)
    print(f"age: {user_input.age}")

except ValidationError as e:
    print(f"验证失败：{e}")

# 数据传入和传出：json 和 model互转
try:
    # model 转 json str： model_dump_json
    user_json = user_input.model_dump_json()
    print(f"转json {user_json}")

    # model 转 json：model_json_schema()
    json = UserInput.model_json_schema()

    # json 转 model
    # model_validate_json：接收 json str
    # model_validate：接受 json
    user_model = UserInput.model_validate(form_data)
    print(f"转model {user_model.name}")
except Exception as e:
    print(f"转化失败：{e}")
