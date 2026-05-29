class FrameStore:
    def __init__(self) -> None:
        self.frames: dict[str, bytes] = {}

    def put(self, frame_id: str, content: bytes) -> None:
        self.frames[frame_id] = content

    def get(self, frame_id: str) -> bytes | None:
        return self.frames.get(frame_id)


frame_store = FrameStore()
