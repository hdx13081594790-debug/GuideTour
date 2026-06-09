from fastapi import Header

# 鉴权占位层。
#
# 当前 MVP 没有强制 JWT/设备 token 校验，只把 Authorization 头取出来。
# 后续如果接眼镜设备注册、用户登录或后台权限，路由层可以 Depends 这个函数，
# 在这里统一校验 token，而不需要把鉴权逻辑散落到各个接口里。


async def optional_device_token(authorization: str | None = Header(default=None)) -> str | None:
    # 返回原始 Authorization 值给调用方。当前没有解析 Bearer/JWT。
    return authorization
