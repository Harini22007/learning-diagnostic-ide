import os
import sys
from collections import Counter

# Ensure backend directory is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from schemas import (
    LearningMap,
    Topic,
    Concept,
    DiagnosticQuestion,
    StudentResponseItem,
    DimensionScores,
    AnswerSheetAnalysis,
    ExtractedQuestionAnswer,
)
from analyzer import (
    clean_metadata_str,
    is_pure_metadata,
    clean_learning_map,
    _pre_filter_study_material_text,
    generate_diagnostic_assessment,
    validate_diagnostic_question,
    validate_and_filter_questions,
    evaluate_single_answer,
    diagnose_learning,
)

def test_point_1_learning_map_quality():
    print("\n==================================================")
    print("TEST 1: FIX LEARNING MAP QUALITY & METADATA FILTERING")
    print("==================================================")

    # Specific requirement check:
    # "AL2311-DATA STRUCTURES AND ALGORITHM DESIGN 5 M.Santhanala..." must NOT become a concept.
    bad_concept = "AL2311-DATA STRUCTURES AND ALGORITHM DESIGN 5 M.Santhanala.."
    assert is_pure_metadata(bad_concept), f"'{bad_concept}' should be identified as pure metadata!"

    # Test individual metadata components
    assert is_pure_metadata("AL2311"), "Course code AL2311 should be metadata"
    assert is_pure_metadata("CS8391"), "Course code CS8391 should be metadata"
    assert is_pure_metadata("M.Santhanala"), "Author M.Santhanala should be metadata"
    assert is_pure_metadata("Dr. John Doe"), "Author Dr. John Doe should be metadata"
    assert is_pure_metadata("Prof. Smith"), "Author Prof. Smith should be metadata"
    assert is_pure_metadata("Page 12 of 45"), "Page number should be metadata"
    assert is_pure_metadata("Slide 4"), "Slide number should be metadata"
    assert is_pure_metadata("Unit - 1"), "Unit number should be metadata"
    assert is_pure_metadata("lecture_notes.pdf"), "Filename should be metadata"
    assert is_pure_metadata("L T P C 3 0 0 3"), "LTPC marker should be metadata"
    assert is_pure_metadata("Regulation 2021"), "Regulation marker should be metadata"

    # Valid academic concepts must NOT be flagged as metadata
    assert not is_pure_metadata("Binary Search Trees"), "'Binary Search Trees' should be a valid concept"
    assert not is_pure_metadata("Dijkstra Shortest Path Algorithm"), "'Dijkstra Shortest Path Algorithm' should be valid"
    assert not is_pure_metadata("Asymptotic Complexity Analysis"), "'Asymptotic Complexity Analysis' should be valid"

    # Test clean_learning_map rejects bad concepts and cleans topics
    dirty_lm = LearningMap(
        subject="AL2311-DATA STRUCTURES AND ALGORITHM DESIGN 5 M.Santhanala..",
        topics=[
            Topic(
                topic="Unit - 1 AL2311 Fundamentals",
                concepts=[
                    Concept(name="AL2311-DATA STRUCTURES AND ALGORITHM DESIGN 5 M.Santhanala..", prerequisites=[], related_concepts=[]),
                    Concept(name="M.Santhanala", prerequisites=[], related_concepts=[]),
                    Concept(name="Page 5", prerequisites=[], related_concepts=[]),
                    Concept(name="unit1_notes.pdf", prerequisites=[], related_concepts=[]),
                    Concept(name="Binary Search Trees", prerequisites=["AL2311", "Linear Linked Lists"], related_concepts=["Page 1", "AVL Trees"]),
                    Concept(name="AVL Trees", prerequisites=["Binary Search Trees"], related_concepts=[]),
                ]
            ),
            Topic(
                topic="AL2311 Course Objectives and Faculty Dept of CSE",
                concepts=[
                    Concept(name="Prepared by Prof. Rao", prerequisites=[], related_concepts=[]),
                ]
            )
        ]
    )

    clean_lm = clean_learning_map(dirty_lm)
    print(f"Cleaned Subject: {clean_lm.subject}")
    assert "AL2311" not in clean_lm.subject
    assert "Santhanala" not in clean_lm.subject

    all_concepts = [c.name for t in clean_lm.topics for c in t.concepts]
    print(f"Extracted Clean Concepts: {all_concepts}")

    assert "AL2311-DATA STRUCTURES AND ALGORITHM DESIGN 5 M.Santhanala.." not in all_concepts
    assert "M.Santhanala" not in all_concepts
    assert "Page 5" not in all_concepts
    assert "unit1_notes.pdf" not in all_concepts
    assert "Prepared by Prof. Rao" not in all_concepts
    assert "Binary Search Trees" in all_concepts
    assert "AVL Trees" in all_concepts

    for t in clean_lm.topics:
        assert "AL2311" not in t.topic
        for c in t.concepts:
            assert "AL2311" not in c.prerequisites
            assert "Page 1" not in c.related_concepts

    print("[PASS] Test 1: Learning Map Quality & Metadata Filtering verified successfully!")
    return clean_lm


def test_point_2_and_3_question_quality_and_validation(clean_lm):
    print("\n==================================================")
    print("TEST 2 & 3: DIAGNOSTIC QUESTION QUALITY & VALIDATION")
    print("==================================================")

    os.environ["MOCK_LLM"] = "true"
    questions = generate_diagnostic_assessment(clean_lm)

    print(f"Generated questions count: {len(questions)}")
    assert len(questions) == 8, f"Expected exactly 8 questions, got {len(questions)}"

    # Check that dimensions are present internally
    dims_found = Counter(q.dimension for q in questions)
    print(f"Dimension distribution: {dict(dims_found)}")
    assert dims_found["Concept Understanding"] == 2
    assert dims_found["Logical Reasoning"] == 2
    assert dims_found["Problem Solving"] == 2
    assert dims_found["Practical/Application"] == 2

    # Check internal fields
    for q in questions:
        assert q.id
        assert q.topic
        assert q.concept
        assert q.difficulty in ["beginner", "intermediate", "advanced"]
        assert q.dimension in ["Concept Understanding", "Logical Reasoning", "Problem Solving", "Practical/Application"]
        assert q.marks > 0
        assert q.expected_answer, f"Question {q.id} missing expected_answer"
        assert q.evaluation_criteria, f"Question {q.id} missing evaluation_criteria"

        # Check purity: no metadata garbage in question or concept
        for meta_pattern in ["AL2311", "Santhanala", "Page", "Slide", "Unit - 1", "L T P C"]:
            assert meta_pattern.lower() not in q.question.lower(), f"Question {q.id} contains metadata: {meta_pattern}"
            assert meta_pattern.lower() not in q.concept.lower(), f"Concept {q.concept} contains metadata: {meta_pattern}"

    # Test question quality validation function
    valid_concepts = {c.name for t in clean_lm.topics for c in t.concepts}
    seen = set()

    # Valid question should pass
    is_valid, reason = validate_diagnostic_question(questions[0], valid_concepts, seen)
    assert is_valid, f"Valid question failed validation: {reason}"

    # Question with garbage metadata should FAIL validation
    garbage_q = DiagnosticQuestion(
        id="diag_bad",
        topic="Data Structures",
        concept="Binary Search Trees",
        difficulty="intermediate",
        dimension="Concept Understanding",
        marks=5,
        question="According to AL2311 Unit - 1 by Santhanala, what is a tree?",
        expected_answer="A tree is a hierarchical data structure.",
        evaluation_criteria="Accurate definition of tree.",
    )
    is_garbage_valid, g_reason = validate_diagnostic_question(garbage_q, valid_concepts, seen)
    assert not is_garbage_valid, "Question with metadata garbage should have failed validation!"
    print(f"Garbage question correctly rejected: {g_reason}")

    # Question with invalid dimension should FAIL validation
    invalid_dim_q = DiagnosticQuestion(
        id="diag_bad_dim",
        topic="Data Structures",
        concept="Binary Search Trees",
        difficulty="intermediate",
        dimension="Random Trivia",
        marks=5,
        question="What year was the binary search tree invented?",
        expected_answer="It was invented around 1960.",
        evaluation_criteria="Accurate year.",
    )
    is_dim_valid, dim_reason = validate_diagnostic_question(invalid_dim_q, valid_concepts, seen)
    assert not is_dim_valid, "Question with invalid dimension should have failed validation!"
    print(f"Invalid dimension question correctly rejected: {dim_reason}")

    print("[PASS] Test 2 & 3: Diagnostic Question Quality & Validation verified successfully!")
    return questions


def test_point_4_5_6_scoring_and_dimension_calculations(clean_lm, questions):
    print("\n==================================================")
    print("TEST 4, 5 & 6: INDEPENDENT RUBRIC SCORING (NO 84% BUG)")
    print("==================================================")

    # Create a realistic test student profile with GENUINELY DIFFERENT performance:
    # Q1 (Concept Understanding): Thorough, comprehensive response -> should receive high marks (~90-100%)
    # Q2 (Concept Understanding): Good conceptual definition -> should receive good marks (~70-85%)
    # Q3 (Logical Reasoning): Partial, shallow response -> should receive low/developing marks (~20-40%)
    # Q4 (Logical Reasoning): Blank/omitted response -> should receive 0 marks (0%)
    # Q5 (Problem Solving): Average troubleshooting response -> should receive partial marks (~50-60%)
    # Q6 (Problem Solving): Solid diagnostic steps -> should receive strong marks (~80-90%)
    # Q7 (Practical/Application): Strong realistic implementation response -> should receive high marks (~85-95%)
    # Q8 (Practical/Application): Good response -> should receive good marks (~75-85%)

    student_answers = [
        StudentResponseItem(
            question_id=questions[0].id,
            student_answer="A binary search tree is defined as a node-based hierarchical data structure where each node stores a key such that all keys in the left subtree are smaller than the node's key, and all keys in the right subtree are greater. Its primary purpose in algorithm design is to facilitate fast logarithmic searching, insertion, and ordered traversal."
        ),
        StudentResponseItem(
            question_id=questions[1].id,
            student_answer="The primary characteristics of binary search trees are the binary search invariant and node pointers, distinguishing it from linear arrays."
        ),
        StudentResponseItem(
            question_id=questions[2].id,
            student_answer="Pointers are used to link nodes together in memory." # Missing causal chain and dependency reasoning
        ),
        StudentResponseItem(
            question_id=questions[3].id,
            student_answer="" # Blank response -> 0 score
        ),
        StudentResponseItem(
            question_id=questions[4].id,
            student_answer="I would check the inputs and test boundary cases to isolate the bug."
        ),
        StudentResponseItem(
            question_id=questions[5].id,
            student_answer="To resolve edge case violations, the systematic procedure is: 1. Verify input preconditions and null checks. 2. Trace intermediate state invariants and verify balance conditions. 3. Execute unit boundary test cases and isolate the discrepancy."
        ),
        StudentResponseItem(
            question_id=questions[6].id,
            student_answer="In real-world production database systems, binary search trees and balanced variants are implemented as in-memory indexing engines to provide sub-millisecond query lookup latency with predictable O(log n) performance trade-offs."
        ),
        StudentResponseItem(
            question_id=questions[7].id,
            student_answer="Integrate into a production service with structured interfaces, handling memory allocation trade-offs and error recovery."
        ),
    ]

    # Evaluate each answer independently
    evaluated_results = [evaluate_single_answer(q, ans.student_answer) for q, ans in zip(questions, student_answers)]

    print("\nIndividual Question Scores:")
    percentages = []
    for eq in evaluated_results:
        pct = eq.percentage
        percentages.append(pct)
        print(f"  {eq.question_id} ({eq.learning_dimension}): {eq.marks_awarded}/{eq.marks_possible} Marks ({pct}%) | Rubric: {eq.rubric_evaluation[:60]}...")

    # Assert that question scores are NOT artificially identical (~84%)
    unique_pcts = set(percentages)
    print(f"\nUnique score percentages: {unique_pcts}")
    assert len(unique_pcts) >= 4, f"Scores are still artificially similar! Only {len(unique_pcts)} unique percentages: {unique_pcts}"

    # Verify blank answer got 0
    assert evaluated_results[3].marks_awarded == 0.0, "Blank answer should have received 0 marks!"
    assert evaluated_results[3].percentage == 0.0

    # Verify excellent answer got high score (> 80%)
    assert evaluated_results[0].percentage >= 80.0, f"Expected Q1 to score >= 80%, got {evaluated_results[0].percentage}%"

    # Verify poor answer got low score (< 50%)
    assert evaluated_results[2].percentage < 50.0, f"Expected Q3 to score < 50%, got {evaluated_results[2].percentage}%"

    # Now run full diagnosis synthesis
    diagnosis = diagnose_learning(clean_lm, questions, student_answers)

    dim_scores = diagnosis.dimension_scores or diagnosis.dimension_averages
    print(f"\nCalculated Dimension Scores:")
    print(f"  Concept Understanding: {dim_scores.concept_understanding}%")
    print(f"  Logical Reasoning:     {dim_scores.logical_reasoning}%")
    print(f"  Problem Solving:       {dim_scores.problem_solving}%")
    print(f"  Practical/Application: {dim_scores.application}%")

    # Assert dimension scores are NOT all ~84%!
    assert not (
        82 <= dim_scores.concept_understanding <= 86
        and 82 <= dim_scores.logical_reasoning <= 86
        and 82 <= dim_scores.problem_solving <= 86
        and 82 <= dim_scores.application <= 86
    ), "THE 84% PROBLEM STILL EXISTS: All 4 dimensions scored approximately 84%!"

    # Assert that dimensions differ widely according to student responses:
    # Logical reasoning should be much lower than Concept Understanding
    assert dim_scores.logical_reasoning < dim_scores.concept_understanding, (
        f"Logical Reasoning ({dim_scores.logical_reasoning}%) should be lower than Concept Understanding ({dim_scores.concept_understanding}%)"
    )
    assert dim_scores.logical_reasoning < 40, f"Logical reasoning should be low (< 40%), got {dim_scores.logical_reasoning}%"
    assert dim_scores.application >= 60, f"Practical application should be moderate/solid (>= 60%), got {dim_scores.application}%"
    assert dim_scores.problem_solving >= 75, f"Problem solving should be solid (>= 75%), got {dim_scores.problem_solving}%"

    # Verify Concept Scores calculated from question evidence
    assert len(diagnosis.concept_scores) > 0, "No concept scores were computed!"
    print(f"\nConcept Scores from Question Evidence: {[f'{cs.concept}: {cs.percentage}% ({cs.performance_level})' for cs in diagnosis.concept_scores]}")

    print("[PASS] Test 4, 5 & 6: Independent rubric evaluation & mathematical dimension calculations verified!")
    return diagnosis


def test_point_7_8_9_10_diagnosis_evidence_and_no_contradictions(clean_lm, questions):
    print("\n==================================================")
    print("TEST 7, 8, 9 & 10: EVIDENCE-BASED ROOT CAUSES & UI CONSISTENCY")
    print("==================================================")

    # Scenario A: Student with clear friction in Logical Reasoning & Answer Sheet corroboration
    mock_sheet = AnswerSheetAnalysis(
        raw_evidence_summary="Previous midterm exam extracted 2 responses.",
        questions=[
            ExtractedQuestionAnswer(
                question_text="Explain dependency of AVL Trees on BST.",
                student_answer="They are basically the same process.",
                marks_allocated=5.0,
                marks_awarded=1.0,
                ai_interpretation="Confused stage dependencies.",
            )
        ],
        identified_weakness_signals=["AVL Trees", "Binary Search Trees"],
        notes="Historical test evidence.",
    )

    weak_student_answers = [
        StudentResponseItem(question_id=questions[0].id, student_answer="Binary search tree definition is sorted."),
        StudentResponseItem(question_id=questions[1].id, student_answer="Tree nodes have keys."),
        StudentResponseItem(question_id=questions[2].id, student_answer="Pointers connect nodes."),
        StudentResponseItem(question_id=questions[3].id, student_answer=""), # Blank
        StudentResponseItem(question_id=questions[4].id, student_answer="I would check error logs."),
        StudentResponseItem(question_id=questions[5].id, student_answer="Test boundary conditions."),
        StudentResponseItem(question_id=questions[6].id, student_answer="Used in database indexing systems with latency trade-offs."),
        StudentResponseItem(question_id=questions[7].id, student_answer="Deploy as an in-memory cache."),
    ]

    diag_with_sheet = diagnose_learning(
        clean_lm, questions, weak_student_answers, answer_sheet_analysis=mock_sheet
    )

    # Check root causes require evidence
    assert len(diag_with_sheet.possible_root_causes) > 0, "Missing root causes!"
    for rc in diag_with_sheet.possible_root_causes:
        print(f"Root Cause: {rc.root_cause} | Confidence: {rc.confidence_level} | Evidence count: {len(rc.supporting_evidence)}")
        assert len(rc.supporting_evidence) > 0, "Root cause must have supporting evidence!"
        assert rc.confidence_level in ["High", "Medium", "Low"], f"Invalid confidence level: {rc.confidence_level}"
        # Cautious wording check
        assert any(cw in rc.root_cause.lower() for cw in ["responses indicate", "evidence suggests", "potential friction", "possible"]), (
            f"Root cause does not use cautious wording: {rc.root_cause}"
        )

    # Check previous answer sheet integration
    assert diag_with_sheet.previous_evidence_summary is not None, "Missing previous_evidence_summary!"
    assert diag_with_sheet.current_evidence_summary is not None, "Missing current_evidence_summary!"
    assert diag_with_sheet.combined_conclusion is not None, "Missing combined_conclusion!"
    print(f"Previous Evidence: {diag_with_sheet.previous_evidence_summary}")
    print(f"Current Evidence:  {diag_with_sheet.current_evidence_summary}")
    print(f"Combined Result:   {diag_with_sheet.combined_conclusion}")

    # Scenario B: High performing student -> verify "No clear prerequisite gap established"
    def get_solid_answer(q):
        if q.dimension == "Concept Understanding":
            return f"The concept of {q.concept} is defined as a hierarchical data structure algorithm used to organize and optimize search operations with logarithmic bounds."
        elif q.dimension == "Logical Reasoning":
            return f"Because tree height directly causes worst-case latency to degrade, rotations ensure balance invariants; therefore query performance depends on maintaining height constraints."
        elif q.dimension == "Problem Solving":
            return f"To isolate the defect, I will check boundary cases, verify null pointers, test rotation invariants, and debug step by step across edge conditions."
        else: # Practical/Application
            return f"In real-world production database systems, we implement {q.concept} as an in-memory cache index to minimize query latency and scale network throughput."

    solid_student_answers = [
        StudentResponseItem(
            question_id=q.id,
            student_answer=get_solid_answer(q)
        )
        for q in questions
    ]

    diag_solid = diagnose_learning(clean_lm, questions, solid_student_answers)
    solid_rcs = [rc.root_cause for rc in diag_solid.possible_root_causes]
    print(f"\nSolid Student Root Causes: {solid_rcs}")

    # Verify no fabricated prerequisite gaps when evidence is insufficient
    assert any("no clear prerequisite gap established" in rc.lower() for rc in solid_rcs), (
        f"Expected 'No clear prerequisite gap established' for solid student, got: {solid_rcs}"
    )

    # Check for contradictions in solid diagnosis:
    # A score >= 75% must NOT be called a "significant weakness" in summary
    assert "significant weakness" not in diag_solid.overall_summary.lower(), (
        "CONTRADICTION FOUND: High scores were called a 'significant weakness'!"
    )
    print(f"Solid student overall summary: {diag_solid.overall_summary}")

    print("[PASS] Test 7, 8, 9 & 10: Evidence-based root causes, previous sheet integration, and contradiction removal verified!")


if __name__ == "__main__":
    clean_map = test_point_1_learning_map_quality()
    diag_questions = test_point_2_and_3_question_quality_and_validation(clean_map)
    test_point_4_5_6_scoring_and_dimension_calculations(clean_map, diag_questions)
    test_point_7_8_9_10_diagnosis_evidence_and_no_contradictions(clean_map, diag_questions)

    print("\n***************************************************")
    print("ALL 12 REQUIREMENTS TEST SUITE PASSED PERFECTLY!")
    print("***************************************************\n")
