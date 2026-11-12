class DependencyGraph:

    @staticmethod
    def build(provider_statuses: list[dict]) -> dict:
        nodes = [
            "Agent",
            "AgentVersion",
            "TestRun",
            "EvaluationCase",
            "EvaluationResult",
            "Finding",
            "RiskScore",
            "Certificate",
            "ExecutionTrace",
            *[status["provider"] for status in provider_statuses]
        ]

        edges = [
            {"from": "Agent", "to": "AgentVersion"},
            {"from": "AgentVersion", "to": "TestRun"},
            {"from": "TestRun", "to": "EvaluationCase"},
            {"from": "TestRun", "to": "ExecutionTrace"},
            {"from": "TestRun", "to": "Finding"},
            {"from": "TestRun", "to": "RiskScore"},
            {"from": "TestRun", "to": "Certificate"},
        ]

        for provider in provider_statuses:
            edges.append({
                "from": provider["provider"],
                "to": "AgentVersion"
            })
            edges.append({
                "from": provider["provider"],
                "to": "TestRun"})

        return {
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "generated_by": "DependencyGraph",
                "description": "AAOS execution and provider dependency graph"
            }
        }
