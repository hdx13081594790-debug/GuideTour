from app.schemas.location import LocationState, LocationUpdateRequest


class InMemoryLocationStore:
    def __init__(self) -> None:
        self._data: dict[str, LocationState] = {}

    def update(self, payload: LocationUpdateRequest) -> LocationState:
        state = LocationState(
            session_id=payload.session_id,
            device_id=payload.device_id,
            location=payload.location,
            heading=payload.heading,
            pitch=payload.pitch,
            roll=payload.roll,
            accuracy_meters=payload.accuracy_meters,
        )
        self._data[payload.session_id] = state
        return state

    def get(self, session_id: str) -> LocationState | None:
        return self._data.get(session_id)


location_store = InMemoryLocationStore()
