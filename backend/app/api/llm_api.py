from fastapi import APIRouter
from backend.app.services.llm_router.health_monitor import HealthMonitor
from backend.app.services.llm_router.model_selector import ModelSelector
from backend.app.engines.dependency_graph import DependencyGraph

router = APIRouter(
    prefix="/llm",
    tags=["LLM Router"]
)


@router.get("/providers")
def get_providers():
    return HealthMonitor.get_all_provider_statuses()


@router.get("/providers/available")
def get_available_providers():
    return {
        "available_providers": HealthMonitor.get_available_providers()
    }


@router.get("/graph")
def get_provider_graph():
    statuses = HealthMonitor.get_all_provider_statuses()
    return DependencyGraph.build(statuses)


@router.post("/select")
def select_provider(prompt: str):
    available_providers = HealthMonitor.get_available_providers()
    selected_provider = ModelSelector.select_provider(
        available_providers,
        prompt
    )
    return {
        "prompt": prompt,
        "selected_provider": selected_provider,
        "available_providers": available_providers
    }
