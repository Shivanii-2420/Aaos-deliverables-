import sqlite3
import json

conn = sqlite3.connect('aaos.db')
c = conn.cursor()

c.execute(
    'SELECT id, test_run_id, expected_response, actual_response, provider, exact_match_score, semantic_similarity_score, hallucination_score, hallucination_detected, score FROM evaluation_results'
)

rows = c.fetchall()

for r in rows:

    print(
        f"ID={r[0]}, "
        f"run={r[1]}, "
        f'expected="{r[2]}", '
        f'actual="{r[3]}", '
        f'provider={r[4]}, '
        f'metrics={r[5]}, '
        f'score={r[6]}'
    )

conn.close()
