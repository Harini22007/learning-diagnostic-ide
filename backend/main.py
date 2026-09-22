import os
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from schemas import (
    AnalyzeMaterialRequest,
    AnalyzeMaterialResponse,
    LearningMap,
    AnalyzeAnswerSheetRequest,
    AnalyzeAnswerSheetResponse,
    GenerateAssessmentRequest,
    GenerateAssessmentResponse,
    DiagnoseRequest,
    CombinedDiagnosisResponse,
    GenerateInterventionRequest,
    GenerateInterventionResponse,
    GenerateReassessmentRequest,
    GenerateReassessmentResponse,
    EvaluateReassessmentRequest,
    EvaluateReassessmentResponse,
)
from analyzer import (
    analyze_study_material,
    analyze_previous_answer_sheet,
    generate_diagnostic_assessment,
    diagnose_learning,
    generate_personalized_intervention,
    generate_reassessment,
    evaluate_reassessment,
)

load_dotenv()

app = FastAPI(
    title="AI Study Weakness Detector - Backend API",
    description="Full diagnostic pipeline: Learning Map, Answer Sheet analysis, Diagnostic Assessment, Diagnosis, Intervention, Reassessment, and Learning Profile.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
def read_root():
    return {
        "status": "healthy",
        "service": "AI Study Weakness Detector API",
        "version": "2.0.0",
        "endpoints": {
            "health": "/health",
            "analyze_material": "POST /analyze-material",
            "analyze_answer_sheet": "POST /analyze-answer-sheet",
            "generate_assessment": "POST /generate-assessment",
            "diagnose": "POST /diagnose",
            "generate_intervention": "POST /generate-intervention",
            "generate_reassessment": "POST /generate-reassessment",
            "evaluate_reassessment": "POST /evaluate-reassessment",
        },
    }


@app.get("/health", tags=["Health"])
def health_check():
    gemini_set = bool(os.getenv("GEMINI_API_KEY", "").strip())
    openai_set = bool(os.getenv("OPENAI_API_KEY", "").strip())
    mock_set = os.getenv("MOCK_LLM", "false").strip().lower() in ("true", "1", "yes")

    return {
        "status": "ok",
        "version": "2.0.0",
        "configured_providers": {
            "gemini": gemini_set,
            "openai": openai_set,
            "mock_mode": mock_set,
        },
    }


# =========================================================
# 1. Study Material Analysis (Phase 1)
# =========================================================

@app.post(
    "/analyze-material",
    response_model=AnalyzeMaterialResponse,
    status_code=status.HTTP_200_OK,
    tags=["Phase 1: Material Analysis"],
)
def handle_analyze_material(payload: AnalyzeMaterialRequest):
    if not payload.text or not payload.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Extracted text cannot be empty. Please upload a PDF containing readable text.",
        )

    try:
        learning_map: LearningMap = analyze_study_material(payload.text)
        return AnalyzeMaterialResponse(
            success=True,
            learning_map=learning_map,
            message="Learning Map successfully generated from study material.",
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing study material: {str(e)}",
        )


# =========================================================
# 2. Previous Answer Sheet Analysis (Phase 2)
# =========================================================

@app.post(
    "/analyze-answer-sheet",
    response_model=AnalyzeAnswerSheetResponse,
    status_code=status.HTTP_200_OK,
    tags=["Phase 2: Answer Sheet Analysis"],
)
def handle_analyze_answer_sheet(payload: AnalyzeAnswerSheetRequest):
    if not payload.text or not payload.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Answer sheet text cannot be empty.",
        )

    try:
        analysis = analyze_previous_answer_sheet(payload.text, payload.learning_map)
        return AnalyzeAnswerSheetResponse(
            success=True,
            analysis=analysis,
            message="Answer sheet analyzed successfully.",
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing answer sheet: {str(e)}",
        )


# =========================================================
# 3. Diagnostic Assessment Generation (Phase 2)
# =========================================================

@app.post(
    "/generate-assessment",
    response_model=GenerateAssessmentResponse,
    status_code=status.HTTP_200_OK,
    tags=["Phase 2: Diagnostic Assessment"],
)
def handle_generate_assessment(payload: GenerateAssessmentRequest):
    try:
        questions = generate_diagnostic_assessment(
            payload.learning_map,
            payload.answer_sheet_analysis,
            payload.study_material_text,
        )
        return GenerateAssessmentResponse(
            success=True,
            questions=questions,
            message="Diagnostic assessment generated successfully.",
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating diagnostic assessment: {str(e)}",
        )


# =========================================================
# 4. Combined Learning Diagnosis (Phase 2)
# =========================================================

@app.post(
    "/diagnose",
    response_model=CombinedDiagnosisResponse,
    status_code=status.HTTP_200_OK,
    tags=["Phase 2: Combined Diagnosis"],
)
def handle_diagnose(payload: DiagnoseRequest):
    if not payload.questions or not payload.student_answers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Questions and student answers are required for diagnosis.",
        )

    try:
        diagnosis = diagnose_learning(
            learning_map=payload.learning_map,
            questions=payload.questions,
            student_answers=payload.student_answers,
            answer_sheet_analysis=payload.answer_sheet_analysis,
        )
        return CombinedDiagnosisResponse(
            success=True,
            diagnosis=diagnosis,
            message="Combined learning diagnosis generated successfully.",
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error producing learning diagnosis: {str(e)}",
        )


# =========================================================
# 5. ONE Personalized Intervention (Phase 2)
# =========================================================

@app.post(
    "/generate-intervention",
    response_model=GenerateInterventionResponse,
    status_code=status.HTTP_200_OK,
    tags=["Phase 2: Personalized Intervention"],
)
def handle_generate_intervention(payload: GenerateInterventionRequest):
    try:
        intervention = generate_personalized_intervention(payload.diagnosis, payload.learning_map)
        return GenerateInterventionResponse(
            success=True,
            intervention=intervention,
            message="Personalized intervention generated successfully.",
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating personalized intervention: {str(e)}",
        )


# =========================================================
# 6. Reassessment Generation & Evaluation (Phase 2)
# =========================================================

@app.post(
    "/generate-reassessment",
    response_model=GenerateReassessmentResponse,
    status_code=status.HTTP_200_OK,
    tags=["Phase 2: Reassessment"],
)
def handle_generate_reassessment(payload: GenerateReassessmentRequest):
    try:
        questions = generate_reassessment(payload.diagnosis, payload.learning_map)
        return GenerateReassessmentResponse(
            success=True,
            questions=questions,
            message="Targeted reassessment generated successfully.",
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating reassessment: {str(e)}",
        )


@app.post(
    "/evaluate-reassessment",
    response_model=EvaluateReassessmentResponse,
    status_code=status.HTTP_200_OK,
    tags=["Phase 2: Reassessment Evaluation"],
)
def handle_evaluate_reassessment(payload: EvaluateReassessmentRequest):
    if not payload.questions or not payload.student_answers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reassessment questions and student answers are required for evaluation.",
        )

    try:
        profile = evaluate_reassessment(
            before_scores=payload.before_scores,
            questions=payload.questions,
            student_answers=payload.student_answers,
            diagnosis=payload.diagnosis,
            learning_map=payload.learning_map,
        )
        return EvaluateReassessmentResponse(
            success=True,
            profile=profile,
            message="Reassessment evaluated successfully.",
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error evaluating reassessment: {str(e)}",
        )


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "127.0.0.1")
    print(f"Starting AI Study Weakness Detector Backend on http://{host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=True)
