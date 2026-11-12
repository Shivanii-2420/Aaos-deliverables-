"""
Direct smoke test: call backend services directly without HTTP.
This avoids server restart/reload issues and tests the full stack.
"""
from pathlib import Path
from dotenv import load_dotenv

# Load environment before importing backend modules
project_root = Path(__file__).resolve().parent
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=False)

# Now import backend modules
from backend.app.database.session import SessionLocal
from backend.app.services.agent_service import AgentService
from backend.app.services.agent_version_service import AgentVersionService
from backend.app.services.test_run_service import TestRunService
from backend.app.services.evaluation_execution_service import EvaluationExecutionService
from backend.app.models.evaluation_case import EvaluationCase

db = SessionLocal()

try:
    print("=== SMOKE TEST (Direct Backend Call) ===\n")
    
    # Step 1: Create agent
    print("[1/5] Creating agent...")
    from backend.app.schemas.agent_schema import AgentCreate
    agent_payload = AgentCreate(name="SmokeTestAgent", owner="test", description="Direct smoke test")
    agent = AgentService.create_agent(db, agent_payload)
    print(f"✓ Agent created: ID={agent.id}\n")
    
    # Step 2: Create version
    print("[2/5] Creating version...")
    from backend.app.schemas.agent_version_schema import AgentVersionCreate
    version_payload = AgentVersionCreate(version="1.0", model_name="azure/gpt-4o-mini")
    version = AgentVersionService.create_version(db, agent.id, version_payload)
    print(f"✓ Version created: ID={version.id}\n")
    
    # Step 3: Create test run
    print("[3/5] Creating test run...")
    test_run = TestRunService.create_test_run(db, version.id)
    print(f"✓ Test run created: ID={test_run.id}\n")
    
    # Step 4: Create evaluation case
    print("[4/5] Creating evaluation case...")
    case = EvaluationCase(
        name="Basic Test",
        prompt="What is 2+2?",
        expected_response="4",
        category="MATH"
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    print(f"✓ Evaluation case created: ID={case.id}\n")
    
    # Step 5: Execute evaluation
    print("[5/5] Executing evaluation...")
    result = EvaluationExecutionService.execute(test_run.id, db)
    print(f"✓ Evaluation executed successfully!")
    print(f"Result: {result}\n")
    
    print("=== SMOKE TEST PASSED ===")
    
except Exception as e:
    import traceback
    print(f"\n✗ Smoke test failed!")
    print(f"Error: {e}")
    traceback.print_exc()
    exit(1)
finally:
    db.close()
