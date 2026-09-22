from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, model_validator


# =========================================================
# Phase 1: Learning Map Schemas (Preserved)
# =========================================================

class Concept(BaseModel):
    name: str = Field(..., description="Name of the specific concept or sub-topic")
    prerequisites: List[str] = Field(
        default_factory=list,
        description="List of prior concepts needed to understand this concept",
    )
    related_concepts: List[str] = Field(
        default_factory=list,
        description="List of directly connected or related concepts in the material",
    )
    difficulty: Optional[str] = Field(
        default=None,
        description="Relative difficulty or complexity level (e.g., beginner, intermediate, advanced)",
    )
    source_reference: Optional[str] = Field(
        default=None,
        description="Source or page reference when reliably identified in the text (e.g., 'Page 2', 'Chapter 3')",
    )


class Topic(BaseModel):
    topic: str = Field(..., description="Main topic or chapter title")
    concepts: List[Concept] = Field(
        default_factory=list,
        description="List of concepts covered under this topic",
    )


class LearningMap(BaseModel):
    subject: str = Field(
        ...,
        description="Overall subject or course area (e.g., 'Computer Science', 'Cell Biology', 'Calculus')",
    )
    topics: List[Topic] = Field(
        default_factory=list,
        description="List of structured topics extracted strictly from the study material",
    )


class AnalyzeMaterialRequest(BaseModel):
    text: str = Field(..., description="Extracted text from the study material PDF")
    filename: Optional[str] = Field(
        default=None,
        description="Original uploaded PDF filename (optional for reference)",
    )


class AnalyzeMaterialResponse(BaseModel):
    success: bool
    learning_map: Optional[LearningMap] = None
    message: Optional[str] = None
    error: Optional[str] = None


# =========================================================
# Phase 2: Previous Answer Sheet Analysis Schemas
# =========================================================

class ExtractedQuestionAnswer(BaseModel):
    question_number: Optional[str] = Field(default=None, description="e.g., 'Q1', '2(b)'")
    question_text: str = Field(..., description="The question extracted from the answer sheet")
    student_answer: str = Field(..., description="Student's handwritten or typed response")
    marks_allocated: Optional[float] = Field(default=None, description="Total possible marks if clearly visible")
    marks_awarded: Optional[float] = Field(default=None, description="Marks given by grader if visible (treated as evidence, not ground truth)")
    teacher_feedback: Optional[str] = Field(default=None, description="Any teacher remarks or corrections noted")
    relevant_topic: Optional[str] = Field(default=None, description="Mapped topic in study material")
    relevant_concept: Optional[str] = Field(default=None, description="Mapped concept in study material")
    evaluation_criteria: Optional[str] = Field(default=None, description="Question-specific criteria derived from study material")
    ai_interpretation: str = Field(..., description="AI assessment of understanding demonstrated in this specific answer")


class AnswerSheetAnalysis(BaseModel):
    raw_evidence_summary: str = Field(..., description="Summary of extracted text evidence from the test/answer sheet")
    questions: List[ExtractedQuestionAnswer] = Field(default_factory=list)
    identified_weakness_signals: List[str] = Field(
        default_factory=list,
        description="Concepts where mistakes or partial understanding were detected",
    )
    notes: Optional[str] = Field(default=None, description="Cautious disclaimer distinguishing evidence vs interpretation")


class AnalyzeAnswerSheetRequest(BaseModel):
    text: str = Field(..., description="Extracted text from the answer sheet PDF/image")
    filename: Optional[str] = Field(default=None)
    learning_map: LearningMap


class AnalyzeAnswerSheetResponse(BaseModel):
    success: bool
    analysis: Optional[AnswerSheetAnalysis] = None
    message: Optional[str] = None
    error: Optional[str] = None


# =========================================================
# Phase 2: Diagnostic Assessment Schemas
# =========================================================

class DiagnosticQuestion(BaseModel):
    id: str = Field(..., description="Unique question ID (e.g., 'diag_1')")
    topic: str = Field(..., description="Mapped topic title from the Learning Map")
    concept: str = Field(..., description="Mapped concept name from the Learning Map")
    difficulty: str = Field(default="intermediate", description="Difficulty level: beginner, intermediate, advanced")
    dimension: str = Field(
        ...,
        description="Learning dimension: Concept Understanding, Logical Reasoning, Problem Solving, or Practical/Application",
    )
    marks: int = Field(default=5, description="Marks allocated for this question")
    question: str = Field(..., description="The diagnostic question prompt presented to the student")
    expected_answer: str = Field(
        default="",
        description="Expected model answer or key points (strictly hidden from student)",
    )
    evaluation_criteria: str = Field(
        default="",
        description="Detailed evaluation rubric criteria (strictly hidden from student)",
    )
    # Backward compatibility fields
    question_text: Optional[str] = Field(default=None)
    learning_dimension: Optional[str] = Field(default=None)
    expected_criteria: Optional[str] = Field(default=None)

    @model_validator(mode="before")
    @classmethod
    def sync_compatibility_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Sync question and question_text
            if "question" in data and not data.get("question_text"):
                data["question_text"] = data["question"]
            elif "question_text" in data and not data.get("question"):
                data["question"] = data["question_text"]

            # Sync dimension and learning_dimension
            if "dimension" in data and not data.get("learning_dimension"):
                data["learning_dimension"] = data["dimension"]
            elif "learning_dimension" in data and not data.get("dimension"):
                data["dimension"] = data["learning_dimension"]

            # Sync evaluation_criteria and expected_criteria
            if "evaluation_criteria" in data and not data.get("expected_criteria"):
                data["expected_criteria"] = data["evaluation_criteria"]
            elif "expected_criteria" in data and not data.get("evaluation_criteria"):
                data["evaluation_criteria"] = data["expected_criteria"]

            if "marks" not in data or data["marks"] is None:
                data["marks"] = 5

            if "expected_answer" not in data or data["expected_answer"] is None:
                data["expected_answer"] = data.get("expected_criteria") or data.get("evaluation_criteria") or "Demonstrates accurate conceptual mastery."
        return data


class GenerateAssessmentRequest(BaseModel):
    learning_map: LearningMap
    study_material_text: Optional[str] = Field(
        default=None,
        description="Extracted text from the study material PDF for grounding questions",
    )
    answer_sheet_analysis: Optional[AnswerSheetAnalysis] = None


class GenerateAssessmentResponse(BaseModel):
    success: bool
    questions: List[DiagnosticQuestion] = Field(default_factory=list)
    message: Optional[str] = None
    error: Optional[str] = None


# =========================================================
# Phase 2: Combined Learning Diagnosis Schemas
# =========================================================

class StudentResponseItem(BaseModel):
    question_id: str
    student_answer: str


class DimensionScores(BaseModel):
    concept_understanding: int = Field(..., ge=0, le=100)
    logical_reasoning: int = Field(..., ge=0, le=100)
    problem_solving: int = Field(..., ge=0, le=100)
    application: int = Field(..., ge=0, le=100)


class EvaluatedQuestionResult(BaseModel):
    question_id: str
    question_text: str
    concept: str
    dimension: str
    student_answer: str
    score: float = Field(..., description="Score awarded based on question criteria")
    marks_possible: float = Field(default=5.0)
    rubric_evaluation: str = Field(..., description="Detailed criteria-based assessment of this response")
    misconceptions_detected: Optional[str] = Field(default=None, description="Specific misconceptions identified, if any")
    # Structured enhancement fields
    topic: Optional[str] = Field(default=None)
    learning_dimension: Optional[str] = Field(default=None)
    marks_awarded: Optional[float] = Field(default=None)
    percentage: Optional[float] = Field(default=None)
    evidence: List[str] = Field(default_factory=list)
    missing_elements: List[str] = Field(default_factory=list)
    misconceptions: List[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def sync_evaluated_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Sync score and marks_awarded
            if "score" in data and ("marks_awarded" not in data or data["marks_awarded"] is None):
                data["marks_awarded"] = data["score"]
            elif "marks_awarded" in data and ("score" not in data or data["score"] is None):
                data["score"] = data["marks_awarded"]

            # Sync dimension and learning_dimension
            if "dimension" in data and not data.get("learning_dimension"):
                data["learning_dimension"] = data["dimension"]
            elif "learning_dimension" in data and not data.get("dimension"):
                data["dimension"] = data["learning_dimension"]

            # Auto calculate percentage
            marks_possible = float(data.get("marks_possible", 5.0) or 5.0)
            score = float(data.get("score", 0.0) or 0.0)
            if "percentage" not in data or data["percentage"] is None:
                data["percentage"] = round((score / marks_possible) * 100, 1) if marks_possible > 0 else 0.0

            # Sync misconceptions list and misconceptions_detected string
            if "misconceptions_detected" in data and data["misconceptions_detected"] and not data.get("misconceptions"):
                data["misconceptions"] = [data["misconceptions_detected"]]
            elif data.get("misconceptions") and not data.get("misconceptions_detected"):
                data["misconceptions_detected"] = "; ".join(data["misconceptions"])
        return data


class ConceptScore(BaseModel):
    topic: str = Field(..., description="Topic name")
    concept: str = Field(..., description="Concept name")
    marks_awarded: float = Field(..., description="Total marks earned across questions for this concept")
    marks_possible: float = Field(..., description="Total possible marks for this concept")
    percentage: float = Field(..., ge=0, le=100, description="Earned percentage")
    performance_level: str = Field(..., description="'Solid', 'Developing', or 'Needs Focus'")
    evidence_count: int = Field(default=1, description="Number of questions assessing this concept")


class PossibleRootCause(BaseModel):
    root_cause: str = Field(..., description="Cautiously phrased root cause (e.g. 'Possible prerequisite gap in...')")
    affected_concept: str = Field(..., description="Concept experiencing friction")
    supporting_evidence: List[str] = Field(default_factory=list, description="Specific observations from answers")
    confidence_level: str = Field(default="Medium", description="'High', 'Medium', or 'Low'")


class TopicDiagnosis(BaseModel):
    topic: str
    concept: str
    dimensions: DimensionScores
    primary_difficulty: str = Field(..., description="Identified area of friction")
    possible_root_cause: str = Field(..., description="Cautiously phrased root cause (e.g., 'Possible prerequisite gap in...')")
    evidence: List[str] = Field(default_factory=list, description="Specific observations from student answers and answer sheet")
    confidence: str = Field(default="Medium", description="'High', 'Medium', or 'Low'")
    missing_elements: List[str] = Field(default_factory=list)
    misconceptions: List[str] = Field(default_factory=list)


class CombinedDiagnosis(BaseModel):
    overall_summary: str = Field(..., description="Cautious evidence-based narrative summary of student learning patterns")
    dimension_scores: Optional[DimensionScores] = Field(default=None, description="Calculated scores across 4 learning dimensions")
    dimension_averages: DimensionScores = Field(..., description="Maintained for backward compatibility")
    concept_scores: List[ConceptScore] = Field(default_factory=list, description="Concept-level performance calculated from question evidence")
    topic_diagnosis: List[TopicDiagnosis] = Field(default_factory=list)
    identified_friction: List[str] = Field(default_factory=list, description="List of specific friction points")
    possible_root_causes: List[PossibleRootCause] = Field(default_factory=list, description="Root causes with supporting evidence and confidence levels")
    prerequisite_gaps: List[str] = Field(default_factory=list)
    recommended_focus: List[str] = Field(default_factory=list, description="Prioritized list of concepts for targeted review")
    recommended_focus_areas: List[str] = Field(default_factory=list, description="Maintained for backward compatibility")
    evaluated_questions: List[EvaluatedQuestionResult] = Field(default_factory=list)
    previous_evidence_summary: Optional[str] = Field(default=None, description="Summary of evidence from previous answer sheet if provided")
    current_evidence_summary: Optional[str] = Field(default=None, description="Summary of evidence from current diagnostic test")
    combined_conclusion: Optional[str] = Field(default=None, description="Cautious combined conclusion across both evidence sources")
    confidence: str = Field(default="Medium", description="Overall confidence level in the diagnosis")

    @model_validator(mode="before")
    @classmethod
    def sync_diagnosis_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Sync dimension_scores and dimension_averages
            if "dimension_scores" in data and data["dimension_scores"] is not None and not data.get("dimension_averages"):
                data["dimension_averages"] = data["dimension_scores"]
            elif "dimension_averages" in data and data["dimension_averages"] is not None and not data.get("dimension_scores"):
                data["dimension_scores"] = data["dimension_averages"]

            # Sync recommended_focus and recommended_focus_areas
            if "recommended_focus" in data and data["recommended_focus"] and not data.get("recommended_focus_areas"):
                data["recommended_focus_areas"] = data["recommended_focus"]
            elif "recommended_focus_areas" in data and data["recommended_focus_areas"] and not data.get("recommended_focus"):
                data["recommended_focus"] = data["recommended_focus_areas"]
        return data


class DiagnoseRequest(BaseModel):
    learning_map: LearningMap
    questions: List[DiagnosticQuestion]
    student_answers: List[StudentResponseItem]
    answer_sheet_analysis: Optional[AnswerSheetAnalysis] = None


class CombinedDiagnosisResponse(BaseModel):
    success: bool
    diagnosis: Optional[CombinedDiagnosis] = None
    message: Optional[str] = None
    error: Optional[str] = None


# =========================================================
# Phase 2: ONE Personalized Intervention Schemas
# =========================================================

class InterventionModule(BaseModel):
    concept: str
    identified_gap: str
    prerequisite_refresher: Optional[str] = None
    core_explanation: str
    misconception_clarification: Optional[str] = None
    worked_example: str
    practice_prompts: List[str] = Field(default_factory=list)


class PersonalizedIntervention(BaseModel):
    title: str
    overview: str
    weakness_focus_summary: Optional[str] = Field(
        default=None,
        description="Summary of student's weakest dimensions targeted by this intervention",
    )
    suggested_learning_sequence: List[str] = Field(
        default_factory=list,
        description="Recommended ordered sequence of concepts/steps to review",
    )
    targeted_modules: List[InterventionModule] = Field(default_factory=list)
    study_recommendations: List[str] = Field(default_factory=list)


class GenerateInterventionRequest(BaseModel):
    diagnosis: CombinedDiagnosis
    learning_map: LearningMap


class GenerateInterventionResponse(BaseModel):
    success: bool
    intervention: Optional[PersonalizedIntervention] = None
    message: Optional[str] = None
    error: Optional[str] = None


# =========================================================
# Phase 2: Reassessment & Before/After Profile Schemas
# =========================================================

class ReassessmentQuestion(BaseModel):
    id: str = Field(..., description="Unique question ID (e.g., 'reassess_q1')")
    target_concept: str
    learning_dimension: str
    question_text: str
    expected_criteria: str
    dimension: Optional[str] = None
    question: Optional[str] = None
    expected_answer: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def sync_reassessment_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "question_text" in data and not data.get("question"):
                data["question"] = data["question_text"]
            elif "question" in data and not data.get("question_text"):
                data["question_text"] = data["question"]
            if "learning_dimension" in data and not data.get("dimension"):
                data["dimension"] = data["learning_dimension"]
            elif "dimension" in data and not data.get("learning_dimension"):
                data["learning_dimension"] = data["dimension"]
            if "expected_criteria" in data and not data.get("expected_answer"):
                data["expected_answer"] = data["expected_criteria"]
            elif "expected_answer" in data and not data.get("expected_criteria"):
                data["expected_criteria"] = data["expected_answer"]
        return data


class GenerateReassessmentRequest(BaseModel):
    diagnosis: CombinedDiagnosis
    learning_map: LearningMap


class GenerateReassessmentResponse(BaseModel):
    success: bool
    questions: List[ReassessmentQuestion] = Field(default_factory=list)
    message: Optional[str] = None
    error: Optional[str] = None


class DimensionChange(BaseModel):
    before: int
    after: int
    change: int
    interpretation: str


class FinalProfileResult(BaseModel):
    growth_summary: str
    before_scores: DimensionScores
    after_scores: DimensionScores
    changes: Dict[str, DimensionChange]
    concepts_improved: List[str] = Field(
        default_factory=list,
        description="Concepts showing clear improvement after reassessment",
    )
    dimensions_improved: List[str] = Field(
        default_factory=list,
        description="Learning dimensions showing growth",
    )
    remaining_difficulties: List[str] = Field(
        default_factory=list,
        description="Areas where the student still requires practice",
    )
    updated_recommendations: List[str] = Field(
        default_factory=list,
        description="Updated actionable recommendations based on remaining needs",
    )
    mastery_note: str = Field(
        default="Measured results reflect current reassessment performance and do not imply permanent ability or mastery."
    )


class EvaluateReassessmentRequest(BaseModel):
    before_scores: DimensionScores
    questions: List[ReassessmentQuestion]
    student_answers: List[StudentResponseItem]
    diagnosis: Optional[CombinedDiagnosis] = None
    learning_map: Optional[LearningMap] = None


class EvaluateReassessmentResponse(BaseModel):
    success: bool
    profile: Optional[FinalProfileResult] = None
    message: Optional[str] = None
    error: Optional[str] = None
