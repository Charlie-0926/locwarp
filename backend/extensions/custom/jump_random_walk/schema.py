from pydantic import BaseModel


class ApplyJumpSettingsRequest(BaseModel):
    jump_random_walk: bool
    jump_random_walk_radius: float
    udid: str | None = None
