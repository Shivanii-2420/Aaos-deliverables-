from backend.app.services.llm_router.fallback import (
    FallbackRouter
)


response = FallbackRouter.generate(
    "What is a home loan?"
)

print(response)