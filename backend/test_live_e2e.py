import httpx

client = httpx.Client(base_url="http://127.0.0.1:8000", timeout=10.0)

# 1. Health
h = client.get("/health")
assert h.status_code == 200, f"Health failed: {h.text}"
print("[PASS] Live FastAPI Health:", h.json())

# 2. Material Analysis
mat_res = client.post("/analyze-material", json={
    "text": "Cellular Biology: Light reactions in thylakoid split water into oxygen and ATP. Calvin cycle fixes CO2 into glucose.",
    "filename": "sample_biology_notes.pdf"
})
assert mat_res.status_code == 200, f"Material analysis failed: {mat_res.text}"
learning_map = mat_res.json()["learning_map"]
print(f"[PASS] Generated Learning Map: {learning_map['subject']} ({len(learning_map['topics'])} topics)")

# 3. Answer Sheet Analysis
sheet_res = client.post("/analyze-answer-sheet", json={
    "text": "Q1: What is function of light reactions? Student Answer: Captures sunlight and splits water.",
    "filename": "sample_answer_sheet.pdf",
    "learning_map": learning_map
})
assert sheet_res.status_code == 200, f"Answer sheet analysis failed: {sheet_res.text}"
sheet_analysis = sheet_res.json()["analysis"]
print("[PASS] Analyzed Answer Sheet:", sheet_analysis["raw_evidence_summary"])

# 4. Generate Diagnostic Assessment with grounding
diag_res = client.post("/generate-assessment", json={
    "learning_map": learning_map,
    "study_material_text": "Cellular Biology thylakoid Calvin cycle...",
    "answer_sheet_analysis": sheet_analysis
})
assert diag_res.status_code == 200, f"Generate assessment failed: {diag_res.text}"
questions = diag_res.json()["questions"]
assert len(questions) == 8, f"Expected 8 questions, got {len(questions)}"
print(f"[PASS] Diagnostic Assessment: {len(questions)} questions generated")
for idx, q in enumerate(questions):
    print(f"   Q{idx+1} [{q['difficulty']} | {q['marks']} Marks]: {q['question'][:60]}...")
    assert q["dimension"] in ["Concept Understanding", "Logical Reasoning", "Problem Solving", "Practical/Application"]
    assert q["expected_answer"]
    assert q["evaluation_criteria"]

# 5. Test assessment generation without answer sheet (optional flow)
diag_direct = client.post("/generate-assessment", json={
    "learning_map": learning_map,
    "study_material_text": "Cellular Biology thylakoid Calvin cycle...",
})
assert diag_direct.status_code == 200
direct_questions = diag_direct.json()["questions"]
assert len(direct_questions) == 8
print(f"[PASS] Direct Diagnostic Assessment (No answer sheet): {len(direct_questions)} questions generated")

print("\nALL LIVE SERVER E2E INTEGRATION FLOWS VERIFIED SUCCESSFULLY!")
