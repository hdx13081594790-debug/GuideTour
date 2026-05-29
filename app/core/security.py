from fastapi import Header


async def optional_device_token(authorization: str | None = Header(default=None)) -> str | None:
    return authorization
