"""FastAPI routes owned entirely by the local extension layer."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Coroutine
from typing import Any

from fastapi import APIRouter, HTTPException

from models.schemas import SimulationState
from .jump_random_walk.schema import ApplyJumpSettingsRequest
from .spiral.schema import SpiralRequest

EngineProvider = Callable[[str | None], Awaitable[Any]]
TaskSpawner = Callable[[Coroutine[Any, Any, Any]], Any]


def build_custom_location_router(
    engine_provider: EngineProvider,
    spawn: TaskSpawner,
) -> APIRouter:
    router = APIRouter()

    @router.post("/apply-jump-settings")
    async def apply_jump_settings(req: ApplyJumpSettingsRequest):
        engine = await engine_provider(req.udid)
        if engine.state not in (SimulationState.LOOPING, SimulationState.MULTI_STOP):
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "invalid_state",
                    "message": "目前不在巡邏或多點導航模式",
                },
            )
        engine.apply_jump_settings(req.jump_random_walk, req.jump_random_walk_radius)
        return {
            "status": "applied",
            "jump_random_walk": req.jump_random_walk,
            "jump_random_walk_radius": req.jump_random_walk_radius,
        }

    @router.post("/spiral")
    async def start_spiral(req: SpiralRequest):
        engine = await engine_provider(req.udid)
        spawn(engine.start_spiral(
            req.center,
            req.radius_m,
            req.spacing_m,
            req.mode,
            speed_kmh=req.speed_kmh,
            speed_min_kmh=req.speed_min_kmh,
            speed_max_kmh=req.speed_max_kmh,
            straight_line=req.straight_line,
            route_engine=req.route_engine,
        ))
        return {
            "status": "started",
            "radius_m": req.radius_m,
            "spacing_m": req.spacing_m,
            "mode": req.mode,
        }

    return router
