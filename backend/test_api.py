import os
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    print("[PASS] Health endpoint test passed.")

def test_empty_text():
    response = client.post("/analyze-material", json={"text": ""})
    assert response.status_code == 400
    assert "Extracted text cannot be empty" in response.json()["detail"]
    print("[PASS] Empty text validation test passed.")

def test_analyze_material_mock():
    # Enable mock for test
    os.environ["MOCK_LLM"] = "true"
    sample_text = """
    --- Page 1 ---
    Subject: Introduction to Data Structures
    Topic: Linear Data Structures
    Arrays are contiguous memory blocks.
    Linked Lists consist of nodes pointing to the next node.
    Prerequisites: Basic Programming, Variables.

    --- Page 2 ---
    Stacks follow Last-In-First-Out (LIFO).
    Queues follow First-In-First-Out (FIFO).
    """
    response = client.post("/analyze-material", json={"text": sample_text, "filename": "sample.pdf"})
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert "learning_map" in res_data
    learning_map = res_data["learning_map"]
    assert "subject" in learning_map
    assert "topics" in learning_map
    assert len(learning_map["topics"]) > 0
    for topic in learning_map["topics"]:
        assert "topic" in topic
        assert "concepts" in topic
        for concept in topic["concepts"]:
            assert "name" in concept
            assert "prerequisites" in concept
            assert "related_concepts" in concept
            assert "difficulty" in concept
    print("[PASS] Material analysis & Learning Map schema test passed.")

if __name__ == "__main__":
    test_health()
    test_empty_text()
    test_analyze_material_mock()
    print("\nAll backend automated tests passed successfully!")
