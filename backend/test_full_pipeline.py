import os
import sys

# Ensure backend directory is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from schemas import (
    LearningMap,
    Topic,
    Concept,
    StudentResponseItem,
    DimensionScores,
)
from analyzer import (
    clean_metadata_str,
    is_pure_metadata,
    clean_learning_map,
    analyze_study_material,
    generate_diagnostic_assessment,
    diagnose_learning,
    generate_personalized_intervention,
    generate_reassessment,
    evaluate_reassessment,
)

def test_metadata_cleaning():
    print("--- 1. Testing Metadata Cleaning ---")
    dirty_title = "AL2311-DATA STRUCTURES AND ALGORITHM DESIGN 5 M.Santhanala.."
    cleaned = clean_metadata_str(dirty_title)
    print(f"Original: {dirty_title}")
    print(f"Cleaned:  {cleaned}")
    assert "AL2311" not in cleaned, "Subject code was not removed!"
    assert "Santhanala" not in cleaned, "Lecturer name was not removed!"
    assert "Data Structures" in cleaned, "Academic subject was lost!"

    # Test pure metadata detection
    assert is_pure_metadata("AL2311"), "Pure subject code not identified!"
    assert is_pure_metadata("M.Santhanala"), "Pure author name not identified!"
    assert is_pure_metadata("Page 5"), "Pure page number not identified!"
    assert not is_pure_metadata("Binary Search Trees"), "Valid academic concept incorrectly flagged as metadata!"

    # Test clean_learning_map with dirty items
    dirty_lm = LearningMap(
        subject="AL2311-DATA STRUCTURES AND ALGORITHM DESIGN 5 M.Santhanala..",
        topics=[
            Topic(
                topic="Unit - 1 AL2311 Fundamentals",
                concepts=[
                    Concept(name="M.Santhanala", prerequisites=[], related_concepts=[]), # Should be dropped
                    Concept(name="Page 5", prerequisites=[], related_concepts=[]),       # Should be dropped
                    Concept(name="Binary Search Trees", prerequisites=["Page 1", "Linear Arrays"], related_concepts=[]),
                ]
            )
        ]
    )
    clean_lm = clean_learning_map(dirty_lm)
    print(f"Cleaned Subject: {clean_lm.subject}")
    print(f"Cleaned Topics: {[t.topic for t in clean_lm.topics]}")
    for t in clean_lm.topics:
        print(f"  Topic '{t.topic}' concepts: {[c.name for c in t.concepts]}")
        for c in t.concepts:
            print(f"    Prereqs for '{c.name}': {c.prerequisites}")
            assert "Page 1" not in c.prerequisites, "Page number remained in prerequisites!"
            assert "M.Santhanala" not in [c.name for c in t.concepts], "Author name was kept as concept!"

    assert "Data Structures" in clean_lm.subject
    print("[PASS] Metadata cleaning passed successfully!\n")
    return clean_lm

def test_full_diagnostic_pipeline(clean_lm):
    print("--- 2. Testing Assessment Generation ---")
    os.environ["MOCK_LLM"] = "true"

    questions = generate_diagnostic_assessment(clean_lm)
    print(f"Generated {len(questions)} diagnostic questions.")
    assert len(questions) >= 6, f"Expected at least 6 questions, got {len(questions)}"

    # Check 4 learning dimensions
    dims = {q.dimension for q in questions}
    print(f"Dimensions tested: {dims}")
    assert "Concept Understanding" in dims
    assert "Logical Reasoning" in dims
    assert "Problem Solving" in dims
    assert "Practical/Application" in dims

    # Verify hidden fields exist
    for q in questions:
        assert q.expected_answer, f"Question {q.id} missing expected_answer"
        assert q.evaluation_criteria, f"Question {q.id} missing evaluation_criteria"
        assert q.marks > 0, f"Question {q.id} has invalid marks"

    print("[PASS] Diagnostic questions generated with all 4 dimensions & hidden criteria.\n")

    print("--- 3. Testing Diagnosis with Evaluated Questions ---")
    student_answers = [
        StudentResponseItem(
            question_id=questions[0].id,
            student_answer="A binary search tree maintains sorted ordering with smaller left and larger right children."
        ),
        StudentResponseItem(
            question_id=questions[1].id,
            student_answer="It allows binary search in logarithmic time."
        ),
        StudentResponseItem(
            question_id=questions[2].id,
            student_answer="Pointers connect nodes." # brief answer -> lower score
        ),
        StudentResponseItem(
            question_id=questions[3].id,
            student_answer="" # no answer -> 0 score
        ),
    ]
    # Fill any remaining with sample answers
    for q in questions[4:]:
        student_answers.append(StudentResponseItem(question_id=q.id, student_answer="Practical applied response for systems."))

    diagnosis = diagnose_learning(clean_lm, questions, student_answers)
    print(f"Overall summary: {diagnosis.overall_summary[:120]}...")
    print(f"Dimension averages: {diagnosis.dimension_averages}")
    print(f"Evaluated questions count: {len(diagnosis.evaluated_questions)}")
    assert len(diagnosis.evaluated_questions) == len(questions), "Not all questions were evaluated!"

    for eq in diagnosis.evaluated_questions:
        print(f"  Q: {eq.question_id} ({eq.dimension}) | Score: {eq.score}/{eq.marks_possible} | Rubric: {eq.rubric_evaluation[:60]}...")
        assert eq.rubric_evaluation, "Missing rubric evaluation!"

    print("[PASS] Diagnosis and evaluated questions generated successfully.\n")

    print("--- 4. Testing ONE Personalized Intervention ---")
    intervention = generate_personalized_intervention(diagnosis, clean_lm)
    print(f"Intervention Title: {intervention.title}")
    print(f"Weakness Focus: {intervention.weakness_focus_summary}")
    print(f"Learning Sequence: {intervention.suggested_learning_sequence}")
    print(f"Targeted Modules: {len(intervention.targeted_modules)}")
    assert intervention.weakness_focus_summary, "Missing weakness focus summary!"
    assert len(intervention.suggested_learning_sequence) > 0, "Missing suggested learning sequence!"
    assert len(intervention.targeted_modules) > 0, "Missing targeted modules!"
    print("[PASS] ONE Personalized Intervention generated targeting weakest dimensions.\n")

    print("--- 5. Testing Reassessment Generation ---")
    reassess_qs = generate_reassessment(diagnosis, clean_lm)
    print(f"Reassessment questions count: {len(reassess_qs)}")
    assert len(reassess_qs) >= 3, "Expected at least 3 reassessment questions"
    for rq in reassess_qs:
        print(f"  Reassessment Q ({rq.learning_dimension}): {rq.question_text[:70]}...")
        assert rq.question_text, "Missing question text"
        assert rq.expected_criteria, "Missing expected criteria"
    print("[PASS] Reassessment questions generated.\n")

    print("--- 6. Testing Reassessment Evaluation & Before/After Profile ---")
    reassess_answers = [
        StudentResponseItem(
            question_id=reassess_qs[0].id,
            student_answer="By strictly adhering to sequential dependencies, the downstream module receives valid inputs and prevents runtime invariant violations."
        ),
        StudentResponseItem(
            question_id=reassess_qs[1].id,
            student_answer="First check input pointer validity and boundary bounds, then trace intermediate state transformations."
        ),
        StudentResponseItem(
            question_id=reassess_qs[2].id,
            student_answer="Implement a cache or indexing structure to reduce lookup overhead in practical workloads."
        ),
    ]

    profile = evaluate_reassessment(
        before_scores=diagnosis.dimension_averages,
        questions=reassess_qs,
        student_answers=reassess_answers,
        diagnosis=diagnosis,
        learning_map=clean_lm,
    )

    print(f"Growth Summary: {profile.growth_summary}")
    print(f"Before Scores: {profile.before_scores}")
    print(f"After Scores:  {profile.after_scores}")
    print("Deltas per dimension:")
    for dim, ch in profile.changes.items():
        print(f"  {dim}: {ch.before}% -> {ch.after}% (Delta: +{ch.change}%) | {ch.interpretation[:60]}...")
        assert ch.change >= 0, "Expected non-negative growth delta!"

    print(f"Concepts Improved: {profile.concepts_improved}")
    print(f"Dimensions Improved: {profile.dimensions_improved}")
    print(f"Remaining Difficulties: {profile.remaining_difficulties}")
    print(f"Updated Recommendations: {profile.updated_recommendations}")

    assert len(profile.concepts_improved) > 0, "Missing concepts_improved!"
    assert len(profile.dimensions_improved) > 0, "Missing dimensions_improved!"
    assert len(profile.remaining_difficulties) > 0, "Missing remaining_difficulties!"
    assert len(profile.updated_recommendations) > 0, "Missing updated_recommendations!"

    print("[PASS] Full pipeline successfully validated end-to-end!")

if __name__ == "__main__":
    lm = test_metadata_cleaning()
    test_full_diagnostic_pipeline(lm)
