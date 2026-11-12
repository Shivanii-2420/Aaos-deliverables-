from backend.app.engines.attack_engine.attack_library import (
    AttackLibrary
)

from backend.app.services.llm_router.fallback import (
    FallbackRouter
)


class AttackExecutor:

    @staticmethod
    def execute():

        attacks = (
            AttackLibrary.get_attacks()
        )

        results = []

        for attack in attacks:

            try:

                response = (
                    FallbackRouter.generate(
                        attack["prompt"]
                    )
                )

                content = response.get(
                    "content",
                    ""
                )

                results.append(
                    {
                        "attack": attack["name"],
                        "prompt": attack["prompt"],
                        "status": "EXECUTED",
                        "response": content
                    }
                )

            except Exception as ex:

                results.append(
                    {
                        "attack": attack["name"],
                        "status": "FAILED",
                        "error": str(ex)
                    }
                )

        return results