from pydantic import BaseModel, Field, model_validator


class ApplyJumpSettingsRequest(BaseModel):
    jump_dwell_motion: bool | None = None
    jump_extra_wait: float | None = Field(default=None, ge=0.0)
    jump_move_seconds: float | None = Field(default=None, ge=0.0)
    # One-release compatibility for the former toggle. The radius is accepted
    # so an old frontend does not fail validation, but no longer affects motion.
    jump_random_walk: bool | None = None
    jump_random_walk_radius: float | None = None
    udid: str | None = None

    @model_validator(mode="after")
    def require_motion_toggle(self) -> "ApplyJumpSettingsRequest":
        if self.jump_dwell_motion is None and self.jump_random_walk is None:
            raise ValueError("jump_dwell_motion is required")
        return self

    @property
    def resolved_motion_enabled(self) -> bool:
        if self.jump_dwell_motion is not None:
            return self.jump_dwell_motion
        return bool(self.jump_random_walk)
