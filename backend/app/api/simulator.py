from typing import Optional
from fastapi import APIRouter, Depends
from backend.app.dependencies import get_repository
from backend.app.repositories.base import BaseRepository
from backend.app.simulator.live_stream import live_simulator
from backend.app.simulator.scenario_generator import ScenarioGenerator

router = APIRouter(prefix="/simulator", tags=["Live Simulator"])

@router.get("/status")
def get_simulator_status():
    return {
        "is_running": live_simulator.is_running,
        "tick_count": live_simulator._counter,
        "interval_seconds": live_simulator._interval_seconds
    }

@router.post("/start")
def start_simulator(interval_seconds: float = 6.0):
    live_simulator.start(interval_seconds=interval_seconds)
    return {
        "message": "Live telemetry simulator started.",
        "is_running": True,
        "interval_seconds": interval_seconds
    }

@router.post("/stop")
def stop_simulator():
    live_simulator.stop()
    return {
        "message": "Live telemetry simulator stopped.",
        "is_running": False
    }

@router.post("/tick")
async def trigger_manual_tick():
    await live_simulator.generate_single_tick()
    return {
        "message": "Manual telemetry tick executed.",
        "tick_count": live_simulator._counter
    }

@router.post("/scenarios/a")
async def run_scenario_a(release_id: str = "rel-payment-1.0.0", repo: BaseRepository = Depends(get_repository)):
    generator = ScenarioGenerator(repo)
    return await generator.run_scenario_a_trusted_release(release_id=release_id)

@router.post("/scenarios/b")
async def run_scenario_b(release_id: str = "rel-payment-1.0.0", repo: BaseRepository = Depends(get_repository)):
    generator = ScenarioGenerator(repo)
    return await generator.run_scenario_b_tampering(release_id=release_id)

@router.post("/scenarios/c")
async def run_scenario_c(release_id: str = "rel-payment-1.0.0", repo: BaseRepository = Depends(get_repository)):
    generator = ScenarioGenerator(repo)
    return await generator.run_scenario_c_vulnerability(release_id=release_id)

@router.post("/scenarios/d")
async def run_scenario_d(release_id: str = "rel-payment-1.0.0", repo: BaseRepository = Depends(get_repository)):
    generator = ScenarioGenerator(repo)
    return await generator.run_scenario_d_missing_provenance(release_id=release_id)

@router.post("/scenarios/e")
async def run_scenario_e(release_id: str = "rel-payment-1.0.0", repo: BaseRepository = Depends(get_repository)):
    generator = ScenarioGenerator(repo)
    return await generator.run_scenario_e_test_failure(release_id=release_id)
