import os
from fastapi.testclient import TestClient
from main import app

os.environ["MOCK_LLM"] = "true"
client = TestClient(app)

def test_diagnostic_question_generation():
    sample_learning_map = {
        "subject": "Operating Systems",
        "topics": [
            {
                "topic": "Process Management",
                "concepts": [
                    {
                        "name": "Process Scheduling",
                        "prerequisites": ["Process State Transition"],
                        "related_concepts": ["Threads", "CPU Utilization"],
                        "difficulty": "intermediate",
                        "source_reference": "Chapter 3",
                    },
                    {
                        "name": "Deadlock Prevention",
                        "prerequisites": ["Mutual Exclusion", "Resource Allocation Graph"],
                        "related_concepts": ["Banker's Algorithm"],
                        "difficulty": "advanced",
                        "source_reference": "Chapter 7",
                    }
                ]
            }
        ]
    }

    # 1. Generate Assessment without answer sheet
    res = client.post("/generate-assessment", json={
        "learning_map": sample_learning_map,
        "study_material_text": "Operating Systems process scheduling ensures optimal CPU utilization. Deadlock occurs under 4 Coffman conditions.",
    })
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()
    assert data["success"] is True
    questions = data["questions"]

    # Verify at least 6-8 questions
    assert len(questions) >= 6, f"Expected at least 6 questions, got {len(questions)}"
    print(f"[PASS] Assessment question count: {len(questions)}")

    required_dimensions = {
        "Concept Understanding",
        "Logical Reasoning",
        "Problem Solving",
        "Practical/Application",
    }
    dimension_counts = {d: 0 for d in required_dimensions}

    for idx, q in enumerate(questions):
        # Verify internal fields are present
        assert "id" in q and q["id"], f"Question {idx} missing id"
        assert "question" in q and q["question"], f"Question {idx} missing question"
        assert "topic" in q and q["topic"], f"Question {idx} missing topic"
        assert "concept" in q and q["concept"], f"Question {idx} missing concept"
        assert "difficulty" in q and q["difficulty"] in ["beginner", "intermediate", "advanced"], f"Question {idx} invalid difficulty: {q.get('difficulty')}"
        assert "dimension" in q, f"Question {idx} missing dimension"
        assert "marks" in q and isinstance(q["marks"], int) and q["marks"] > 0, f"Question {idx} invalid marks: {q.get('marks')}"
        assert "expected_answer" in q and q["expected_answer"], f"Question {idx} missing expected_answer"
        assert "evaluation_criteria" in q and q["evaluation_criteria"], f"Question {idx} missing evaluation_criteria"

        dim = q["dimension"]
        assert dim in required_dimensions, f"Unknown dimension: {dim}"
        dimension_counts[dim] += 1

    # Verify each dimension tested more than once
    for dim, count in dimension_counts.items():
        assert count >= 2, f"Dimension '{dim}' was only tested {count} times (expected >= 2)"
        print(f"[PASS] Dimension '{dim}' tested {count} times")

    # 2. Test with answer sheet analysis as well
    answer_sheet_analysis = {
        "raw_evidence_summary": "Student answered basic scheduling questions but struggled with deadlock.",
        "questions": [],
        "identified_weakness_signals": ["Deadlock Prevention"],
    }
    res_with_sheet = client.post("/generate-assessment", json={
        "learning_map": sample_learning_map,
        "study_material_text": "OS concepts...",
        "answer_sheet_analysis": answer_sheet_analysis,
    })
    assert res_with_sheet.status_code == 200
    sheet_questions = res_with_sheet.json()["questions"]
    assert len(sheet_questions) >= 6
    print(f"[PASS] Assessment generation with answer sheet analysis: {len(sheet_questions)} questions")

    print("\nALL TARGETED DIAGNOSTIC QUESTION GENERATION TESTS PASSED!")

if __name__ == "__main__":
    test_diagnostic_question_generation()
