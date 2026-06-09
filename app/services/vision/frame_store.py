# 眼镜帧缓存。
#
# MVP 中只用内存保存 frame_id -> bytes，用于模拟“先上传帧，再触发拍照/识别”。
# 生产环境应替换为对象存储或消息队列，避免大文件长期占用后端内存。

class FrameStore:
    def __init__(self) -> None:
        self.frames: dict[str, bytes] = {}

    def put(self, frame_id: str, content: bytes) -> None:
        # 保存一帧图片/关键帧内容。
        self.frames[frame_id] = content

    def get(self, frame_id: str) -> bytes | None:
        # 根据 frame_id 取回图片内容，供视觉识别或拍照资产关联。
        return self.frames.get(frame_id)


frame_store = FrameStore()
