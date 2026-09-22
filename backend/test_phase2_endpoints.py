import os
from fastapi.testclient import TestClient
from main import app
from schemas import (
    LearningMap,
    Topic,
    Concept,
    DiagnosticQuestion,
    StudentResponseItem,
    DimensionScores,
)

client = TestClient(app)
os.environ["MOCK_LLM"] = "true"

def run_tests():
    # 1. Health
    res = client.get("/health")
    assert res.status_code == 200
    print("[PASS] Health endpoint")

    # Sample Learning Map
    sample_map = {
        "subject": "Cell Biology",
        "topics": [
            {
                "topic": "Bioenergetics",
                "concepts": [
                    {
                        "name": "Photosynthesis",
                        "prerequisites": ["Chloroplast Structure"],
                        "related_concepts": ["Cellular Respiration"],
                        "difficulty": "intermediate",
                        "source_reference": "Page 1",
                    },
                    {
                        "name": "Cellular Respiration",
                        "prerequisites": ["Photosynthesis"],
                        "related_concepts": [],
                        "difficulty": "intermediate",
                        "source_reference": "Page 2",
                    }
                ]
            }
        ]
    }

    # 2. Analyze Answer Sheet
    res = client.post("/analyze-answer-sheet", json={
        "text": "Q1: Photosynthesis produces energy. Q2: Respiration happens simultaneously.",
        "learning_map": sample_map,
    })
    if res.status_code != 200:
        print("Analyze answer sheet failed:", res.status_code, res.text)
    assert res.status_code == 200
    sheet_data = res.json()
    assert sheet_data["success"] is True
    assert "analysis" in sheet_data
    print("[PASS] POST /analyze-answer-sheet")

    # 3. Generate Assessment
    res = client.post("/generate-assessment", json={
        "learning_map": sample_map,
        "answer_sheet_analysis": sheet_data["analysis"],
    })
    assert res.status_code == 200
    diag_data = res.json()
    assert diag_data["success"] is True
    questions = diag_data["questions"]
    assert len(questions) > 0
    print("[PASS] POST /generate-assessment (Generated", len(questions), "questions)")

    # 4. Diagnose
    student_answers = [
        {"question_id": q["id"], "student_answer": f"Answer demonstrating basic understanding of {q['concept']}."}
        for q in questions
    ]
    res = client.post("/diagnose", json={
        "learning_map": sample_map,
        "questions": questions,
        "student_answers": student_answers,
        "answer_sheet_analysis": sheet_data["analysis"],
    })
    assert res.status_code == 200
    diag_report = res.json()
    assert diag_report["success"] is True
    diagnosis = diag_report["diagnosis"]
    assert "overall_summary" in diagnosis
    assert "topic_diagnosis" in diagnosis
    print("[PASS] POST /diagnose (Generated Combined Diagnosis)")

    # 5. Generate Personalized Intervention
    res = client.post("/generate-intervention", json={
        "diagnosis": diagnosis,
        "learning_map": sample_map,
    })
    assert res.status_code == 200
    interv_data = res.json()
    assert interv_data["success"] is True
    intervention = interv_data["intervention"]
    assert len(intervention["targeted_modules"]) > 0
    print("[PASS] POST /generate-intervention (ONE Unified Intervention)")

    # 6. Generate Reassessment
    res = client.post("/generate-reassessment", json={
        "diagnosis": diagnosis,
        "learning_map": sample_map,
    })
    assert res.status_code == 200
    reassess_data = res.json()
    assert reassess_data["success"] is True
    reassess_questions = reassess_data["questions"]
    assert len(reassess_questions) > 0
    print("[PASS] POST /generate-reassessment (Generated", len(reassess_questions), "reassessment questions)")

    # 7. Evaluate Reassessment & Final Profile
    reassess_answers = [
        {"question_id": rq["id"], "student_answer": "Detailed answer showing sequential reasoning and clear application."}
        for rq in reassess_questions
    ]
    res = client.post("/evaluate-reassessment", json={
        "before_scores": diagnosis["dimension_averages"],
        "questions": reassess_questions,
        "student_answers": reassess_answers,
    })
    assert res.status_code == 200
    eval_data = res.json()
    assert eval_data["success"] is True
    profile = eval_data["profile"]
    assert "growth_summary" in profile
    assert "changes" in profile
    print("[PASS] POST /evaluate-reassessment (Before/After comparison computed)")

    print("\nALL PHASE 2 BACKEND ENDPOINTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
