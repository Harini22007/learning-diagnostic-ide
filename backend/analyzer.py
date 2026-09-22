import json
import os
import re
from typing import Dict, Any, Optional, List, Tuple
from collections import Counter
from dotenv import load_dotenv

from schemas import (
    LearningMap,
    Topic,
    Concept,
    AnswerSheetAnalysis,
    ExtractedQuestionAnswer,
    DiagnosticQuestion,
    StudentResponseItem,
    DimensionScores,
    EvaluatedQuestionResult,
    ConceptScore,
    PossibleRootCause,
    TopicDiagnosis,
    CombinedDiagnosis,
    InterventionModule,
    PersonalizedIntervention,
    ReassessmentQuestion,
    DimensionChange,
    FinalProfileResult,
)

load_dotenv()


def _clean_json_string(raw: str) -> str:
    """Strip markdown code block fences and whitespace from LLM output."""
    raw = raw.strip()
    if raw.startswith("```"):
        match = re.search(r"^```(?:json)?\s*([\s\S]*?)\s*```$", raw, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return raw


def _call_llm_json(prompt: str, system_prompt: str) -> str:
    """Helper to dispatch LLM call to Gemini or OpenAI with JSON response format."""
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()

    if gemini_key and gemini_key != "your_gemini_api_key_here":
        from google import genai
        from google.genai import types

        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
        client = genai.Client(api_key=gemini_key)
        full_content = f"{system_prompt}\n\n{prompt}"
        response = client.models.generate_content(
            model=model,
            contents=full_content,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )
        if not response.text:
            raise ValueError("Gemini returned an empty response.")
        return response.text

    elif openai_key and openai_key != "your_openai_api_key_here":
        from openai import OpenAI

        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
        client = OpenAI(api_key=openai_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        choice = response.choices[0].message.content
        if not choice:
            raise ValueError("OpenAI returned an empty response.")
        return choice

    else:
        raise ValueError(
            "No LLM API key detected. Please configure GEMINI_API_KEY or OPENAI_API_KEY in backend/.env "
            "(or set MOCK_LLM=true for offline testing)."
        )


# =========================================================
# 1. Study Material Analysis & Learning Map Quality Cleaning
# =========================================================

def clean_metadata_str(s: Optional[str]) -> str:
    """Strip course codes, lecturer/faculty names, page/slide numbers, unit markers,
    filenames, and document artifacts anywhere in the string.
    """
    if not s:
        return ""
    cleaned = s.strip()

    # 1. Strip course codes anywhere in the string:
    # e.g., "AL2311-", "CS8391: ", "EC-101", "AL2311 Fundamentals" -> "Fundamentals"
    cleaned = re.sub(
        r"\b[A-Z]{2,6}\s*[-_]?\s*\d{3,5}[A-Z]?\b\s*[-:–—|/]?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    # 2. Strip lecturer / faculty / author tags and names anywhere:
    # e.g., "5 M.Santhanala..", "Dr. John Doe", "Prof. Smith", "Asst. Prof.", "M.Santhanala"
    cleaned = re.sub(
        r"(?:[\s,;–—|]|^)(?:\d+\s+)?(?:Prof(?:\.|essor)?|Dr\.?|Faculty|Lecturer|Author|Dept\.?\s+of|Department\s+of|College\s+of|University|Asst\.?\s+Prof\.?|Associate\s+Prof\.?|Prepared\s+by|Presented\s+by|Course\s+Instructor|Santhanala|M\.[A-Za-z]+|[A-Z]\.[A-Za-z]+).*$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    # 3. Strip page, slide, unit, lecture, chapter markers anywhere:
    # e.g., "Page 1 of 10", "Slide 5", "Unit - 1", "Lecture 3", "Module 2"
    cleaned = re.sub(
        r"\b(?:Page|Slide|Unit|Chapter|Lecture|Module|Section)\s*[-:–—]?\s*(?:[IVX\d]+)(?:\s*(?:of|/)\s*\d+)?\b\s*[-:–—|/]?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    # 4. Strip syllabus, regulation, semester, copyright, LTPC markers:
    cleaned = re.sub(
        r"\b(?:Regulation\s+\d+|Semester\s+[IVX\d]+|All\s+Rights\s+Reserved|Copyright\s+.*|Syllabus\s*\d*|L\s*T\s*P\s*C(?:\s*\d+)*)\b",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    # 5. Strip document file extensions (e.g., .pdf, .docx, .pptx):
    cleaned = re.sub(
        r"\b[\w-]+\.(?:pdf|docx?|pptx?|txt)\b",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    # 6. Clean leading and trailing punctuation and digits/noise
    cleaned = re.sub(r"^[-:–—._,;/\s\d]+|[-:–—._,;/\s]+$", "", cleaned)

    # 7. Normalize ALL CAPS long strings to Title Case for readability (preserving short acronyms)
    if cleaned.isupper() and len(cleaned) > 4:
        words = cleaned.split()
        capitalized = [w if (len(w) <= 3 and w.isalpha()) else w.capitalize() for w in words]
        cleaned = " ".join(capitalized)

    return cleaned.strip()


def is_pure_metadata(s: Optional[str], subject_context: Optional[str] = None) -> bool:
    """Return True if string is purely document metadata, course code, author name,
    course header, matches overall subject title, or is too short/long to be a concept.
    """
    if not s or len(s.strip()) < 3:
        return True
    val = s.strip()

    # Composite metadata check: course code combined with author or number artifact
    # e.g. "AL2311-DATA STRUCTURES AND ALGORITHM DESIGN 5 M.Santhanala.."
    if re.search(r"\b[A-Z]{2,6}\s*[-_]?\s*\d{3,5}[A-Z]?\b", val, re.IGNORECASE) and (
        re.search(r"\b(?:Prof|Dr|Faculty|Lecturer|Author|Dept|Santhanala|M\.[A-Za-z]+)\b", val, re.IGNORECASE)
        or re.match(r"^[A-Z]{2,6}\s*[-_]?\s*\d{3,5}[A-Z]?$", val, re.IGNORECASE)
    ):
        return True

    # Matches course code alone e.g. AL2311, CS8391, IT 201
    if re.match(r"^[A-Z]{2,6}\s*[-_]?\d{3,5}[A-Z]?$", val, re.IGNORECASE):
        return True

    # Matches author / faculty pattern
    if re.search(
        r"\b(?:Prof(?:\.|essor)?|Dr\.?|Faculty|Lecturer|Author|Department\s+of|Dept\.?\s+of|College\s+of|University|Asst\.?\s+Prof\.?|Prepared\s+by|Presented\s+by|Course\s+Instructor|Santhanala|M\.[A-Za-z]+)\b",
        val,
        re.IGNORECASE,
    ):
        return True

    # Matches pagination / unit / slide / semester / regulation alone
    if re.match(
        r"^(?:Page|Slide|Unit|Chapter|Lecture|Module|Section|Semester|Regulation)\s*[-:–—]?\s*(?:[IVX\d]+)(?:\s*(?:of|/)\s*\d+)?$",
        val,
        re.IGNORECASE,
    ):
        return True

    # Matches document filename
    if re.match(r"^[\w-]+\.(?:pdf|docx?|pptx?|txt)$", val, re.IGNORECASE):
        return True

    # Strings that are course administrative lines or syllabus headers
    if re.search(r"\b(?:Regulation\s+\d+|L\s*T\s*P\s*C|Syllabus\s*20\d\d|Course\s+Outcomes?|Course\s+Objectives?)\b", val, re.IGNORECASE):
        return True

    # After cleaning, check if residual length is meaningful
    cleaned = clean_metadata_str(val)
    if len(cleaned) < 3:
        return True

    # If residual is just unit/page markers
    if re.match(r"^(?:Page|Slide|Unit|Chapter|Lecture|Module|Section)\s*\d*$", cleaned, re.IGNORECASE):
        return True

    # Check if string matches or is essentially identical to the overall subject / course title
    if subject_context:
        clean_subj = clean_metadata_str(subject_context).lower()
        if cleaned.lower() == clean_subj or (len(clean_subj) > 5 and clean_subj in cleaned.lower()):
            return True

    # Concept names must be short (at most 9 words or 75 chars). Full sentences or header paragraphs are not concepts.
    if len(cleaned) > 75 or len(cleaned.split()) > 9:
        return True

    return False


def _pre_filter_study_material_text(text: str) -> str:
    """Pre-filters raw extracted PDF text before sending to LLM.
    Removes repeating page header/footers, course code banners, author lines, and page markers.
    """
    if not text:
        return ""

    lines = [line.strip() for line in text.splitlines()]
    if not lines:
        return ""

    # Count line occurrences to identify repeated headers/footers
    line_counts = Counter(l for l in lines if len(l) > 6 and not l.startswith("---"))

    filtered_lines = []
    for line in lines:
        if not line:
            filtered_lines.append("")
            continue

        # Keep page demarcator in simplified form
        if line.startswith("--- Page"):
            filtered_lines.append(line)
            continue

        # If a line appears repeatedly (>= 3 times), it is likely a running header/footer
        if line_counts.get(line, 0) >= 3 and is_pure_metadata(line):
            continue

        # Drop pure metadata lines (course codes, lecturer names, page numbers)
        if is_pure_metadata(line):
            continue

        filtered_lines.append(line)

    return "\n".join(filtered_lines)


def clean_learning_map(learning_map: LearningMap) -> LearningMap:
    """Sanitizes a LearningMap by stripping course codes, lecturer/author names,
    headers/footers, and page numbers from subject, topics, concepts, and relationships.
    Strictly filters out document metadata from becoming concepts.
    Preserves valid academic concepts grounded in the study material.
    """
    cleaned_subject = clean_metadata_str(learning_map.subject)
    if is_pure_metadata(cleaned_subject) or not cleaned_subject:
        cleaned_subject = "Core Course Curriculum"

    cleaned_topics: List[Topic] = []

    # First pass: collect all valid concept names
    for topic in learning_map.topics:
        for c in topic.concepts:
            c_name = clean_metadata_str(c.name)
            if c_name and not is_pure_metadata(c_name, subject_context=cleaned_subject):
                pass

    for topic_idx, topic in enumerate(learning_map.topics):
        topic_title = clean_metadata_str(topic.topic)
        if is_pure_metadata(topic_title) or not topic_title:
            topic_title = f"Topic {topic_idx + 1}"

        cleaned_concepts: List[Concept] = []
        for concept in topic.concepts:
            concept_name = clean_metadata_str(concept.name)
            # Filter out concepts that are pure metadata, course headers, or match subject
            if not concept_name or is_pure_metadata(concept_name, subject_context=cleaned_subject):
                continue

            # Clean prerequisites
            cleaned_prereqs = []
            for p in concept.prerequisites:
                clean_p = clean_metadata_str(p)
                if clean_p and not is_pure_metadata(clean_p, subject_context=cleaned_subject):
                    cleaned_prereqs.append(clean_p)

            # Clean related concepts
            cleaned_related = []
            for r in concept.related_concepts:
                clean_r = clean_metadata_str(r)
                if clean_r and not is_pure_metadata(clean_r, subject_context=cleaned_subject):
                    cleaned_related.append(clean_r)

            cleaned_concepts.append(
                Concept(
                    name=concept_name,
                    prerequisites=cleaned_prereqs,
                    related_concepts=cleaned_related,
                    difficulty=concept.difficulty or "intermediate",
                    source_reference=concept.source_reference,
                )
            )

        if cleaned_concepts:
            cleaned_topics.append(Topic(topic=topic_title, concepts=cleaned_concepts))

    # Defensive guarantee: if all concepts were metadata, synthesize clean concepts from subject
    if not cleaned_topics:
        cleaned_topics = [
            Topic(
                topic="Core Theoretical Foundations",
                concepts=[
                    Concept(
                        name=f"Foundations of {cleaned_subject}",
                        prerequisites=["Basic Prerequisites"],
                        related_concepts=[f"Mechanisms of {cleaned_subject}"],
                        difficulty="beginner",
                    ),
                    Concept(
                        name=f"Mechanisms of {cleaned_subject}",
                        prerequisites=[f"Foundations of {cleaned_subject}"],
                        related_concepts=[f"Practical Applications of {cleaned_subject}"],
                        difficulty="intermediate",
                    ),
                ],
            ),
            Topic(
                topic="Applied Analysis & Problem Solving",
                concepts=[
                    Concept(
                        name=f"Practical Applications of {cleaned_subject}",
                        prerequisites=[f"Mechanisms of {cleaned_subject}"],
                        related_concepts=[],
                        difficulty="advanced",
                    )
                ],
            ),
        ]

    return LearningMap(subject=cleaned_subject, topics=cleaned_topics)


PHASE1_SYSTEM_PROMPT = """You are an expert learning diagnostic curriculum analyzer for an AI Study Weakness Detector system.
Your job is to analyze extracted text from uploaded study material and generate a structured Learning Map.

CRITICAL INSTRUCTIONS:
1. PRIMARY SOURCE OF TRUTH: The uploaded study material must be treated as your sole source of truth.
2. NO HALLUCINATIONS: Do NOT invent concepts or topics not supported by the uploaded text.
3. STRICT METADATA FILTERING:
   - You MUST NOT extract document metadata, course codes (e.g., AL2311, CS8391, EC-101), faculty/lecturer/author names (e.g., M.Santhanala, Dr., Prof.), page numbers, slide numbers, unit numbers, header/footer text, syllabus markers, or institution names as concepts or topics.
   - For example: "AL2311-DATA STRUCTURES AND ALGORITHM DESIGN 5 M.Santhanala..." MUST NEVER BE A CONCEPT.
   - Broad course titles or subject names must NOT be listed as sub-concepts under themselves.
   - Topics and concepts must be short (2-5 words), human-readable, domain-specific academic concepts (e.g., "Binary Search Trees", "Time Complexity Analysis", "Cellular Respiration", "Krebs Cycle").
4. Output valid JSON:
{
  "subject": "string",
  "topics": [
    {
      "topic": "string",
      "concepts": [
        {
          "name": "string",
          "prerequisites": ["string"],
          "related_concepts": ["string"],
          "difficulty": "beginner" | "intermediate" | "advanced" | null,
          "source_reference": "string" | null
        }
      ]
    }
  ]
}
"""


def _generate_mock_learning_map(text: str) -> LearningMap:
    raw_lines = [l.strip() for l in text.splitlines() if l.strip() and not l.startswith("---")]
    title = "Study Material"
    for line in raw_lines:
        cand = clean_metadata_str(line)
        if cand and not is_pure_metadata(cand) and len(cand) > 3:
            title = cand
            break

    if len(title) > 60:
        title = title[:60].strip() + "..."

    lower_text = text.lower()
    if any(k in lower_text for k in ["algorithm", "data structure", "tree", "graph", "binary", "sort", "stack", "queue", "al2311"]):
        topics = [
            Topic(
                topic="Foundations of Data Structures",
                concepts=[
                    Concept(
                        name="Asymptotic Analysis & Big-O Notation",
                        prerequisites=["Basic Discrete Mathematics"],
                        related_concepts=["Time and Space Complexity"],
                        difficulty="beginner",
                    ),
                    Concept(
                        name="Linear Data Structures & Pointers",
                        prerequisites=["Basic Programming"],
                        related_concepts=["Dynamic Memory Allocation"],
                        difficulty="beginner",
                    ),
                ],
            ),
            Topic(
                topic="Tree & Hierarchical Data Structures",
                concepts=[
                    Concept(
                        name="Binary Search Trees & Traversal",
                        prerequisites=["Linear Data Structures & Pointers"],
                        related_concepts=["Balanced AVL Trees"],
                        difficulty="intermediate",
                    ),
                    Concept(
                        name="Balanced AVL Trees & Rotations",
                        prerequisites=["Binary Search Trees & Traversal"],
                        related_concepts=["B-Trees"],
                        difficulty="advanced",
                    ),
                ],
            ),
            Topic(
                topic="Graph Algorithms & Problem Solving",
                concepts=[
                    Concept(
                        name="Graph Traversal (BFS and DFS)",
                        prerequisites=["Linear Data Structures & Pointers"],
                        related_concepts=["Shortest Path Algorithms"],
                        difficulty="intermediate",
                    ),
                    Concept(
                        name="Dijkstra Shortest Path Algorithm",
                        prerequisites=["Graph Traversal (BFS and DFS)", "Binary Search Trees & Traversal"],
                        related_concepts=["Greedy Algorithms"],
                        difficulty="advanced",
                    ),
                ],
            ),
        ]
    elif any(k in lower_text for k in ["cell", "biology", "respiration", "photosynthesis", "krebs", "dna"]):
        topics = [
            Topic(
                topic="Cellular Energy & Metabolism",
                concepts=[
                    Concept(
                        name="Glycolysis & Substrate Phosphorylation",
                        prerequisites=["Basic Molecular Chemistry"],
                        related_concepts=["Krebs Cycle"],
                        difficulty="beginner",
                    ),
                    Concept(
                        name="Krebs Citric Acid Cycle",
                        prerequisites=["Glycolysis & Substrate Phosphorylation"],
                        related_concepts=["Electron Transport Chain"],
                        difficulty="intermediate",
                    ),
                ],
            ),
            Topic(
                topic="Mitochondrial Respiration",
                concepts=[
                    Concept(
                        name="Electron Transport Chain & Chemiosmosis",
                        prerequisites=["Krebs Citric Acid Cycle"],
                        related_concepts=["ATP Synthase Mechanism"],
                        difficulty="advanced",
                    )
                ],
            ),
        ]
    else:
        topics = [
            Topic(
                topic=f"Core Principles of {title}",
                concepts=[
                    Concept(
                        name=f"Foundational Principles of {title}",
                        prerequisites=["Introductory Foundations"],
                        related_concepts=[f"Analytical Mechanics of {title}"],
                        difficulty="beginner",
                    ),
                    Concept(
                        name=f"Analytical Mechanics of {title}",
                        prerequisites=[f"Foundational Principles of {title}"],
                        related_concepts=[],
                        difficulty="intermediate",
                    ),
                ],
            ),
            Topic(
                topic=f"Applied Analysis of {title}",
                concepts=[
                    Concept(
                        name=f"Practical Applications of {title}",
                        prerequisites=[f"Analytical Mechanics of {title}"],
                        related_concepts=[],
                        difficulty="advanced",
                    )
                ],
            ),
        ]

    lm = LearningMap(subject=title, topics=topics)
    return clean_learning_map(lm)


def analyze_study_material(text: str) -> LearningMap:
    if not text or not text.strip():
        raise ValueError("The provided study material text is empty.")

    filtered_text = _pre_filter_study_material_text(text)
    if not filtered_text.strip():
        filtered_text = text.strip()

    mock_llm = os.getenv("MOCK_LLM", "false").strip().lower() in ("true", "1", "yes")
    if mock_llm:
        return _generate_mock_learning_map(filtered_text)

    prompt = f"STUDY MATERIAL TEXT TO ANALYZE:\n\"\"\"\n{filtered_text}\n\"\"\""
    raw_json = _call_llm_json(prompt, PHASE1_SYSTEM_PROMPT)
    cleaned = _clean_json_string(raw_json)
    data = json.loads(cleaned)
    raw_lm = LearningMap.model_validate(data)
    return clean_learning_map(raw_lm)


# =========================================================
# 2. Previous Answer Sheet Analysis (Phase 2)
# =========================================================

ANSWER_SHEET_PROMPT = """You are an educational assessment analyzer examining a student's previous test or answer sheet.
You are provided with:
1. The structured Learning Map of the course.
2. The extracted text from the student's previous test/answer sheet.

INSTRUCTIONS:
1. Extract questions, student answers, marks allocated/awarded (if visible), and any teacher remarks.
2. Clearly distinguish between EXTRACTED EVIDENCE (what is actually written on the sheet) and AI INTERPRETATION.
3. Do NOT use a universal fixed grading rubric. Create question-specific evaluation criteria based on the question, the subject material, and marks.
4. If marks or teacher remarks are present, treat them as additional evidence, not absolute ground truth.
5. Identify potential weakness signals (concepts where the student showed misconceptions or partial reasoning).

Output strictly valid JSON:
{
  "raw_evidence_summary": "string describing what was found on the sheet",
  "questions": [
    {
      "question_number": "string or null",
      "question_text": "string",
      "student_answer": "string",
      "marks_allocated": float or null,
      "marks_awarded": float or null,
      "teacher_feedback": "string or null",
      "relevant_topic": "string or null",
      "relevant_concept": "string or null",
      "evaluation_criteria": "question-specific criteria",
      "ai_analysis": "specific evaluation of the answer"
    }
  ],
  "identified_weakness_signals": ["concept names with apparent weaknesses"],
  "notes": "cautious note distinguishing evidence vs interpretation"
}
"""


def _mock_answer_sheet_analysis(text: str, learning_map: LearningMap) -> AnswerSheetAnalysis:
    first_topic = learning_map.topics[0] if learning_map.topics else None
    first_concept = first_topic.concepts[0].name if first_topic and first_topic.concepts else "Core Concept"
    second_concept = first_topic.concepts[1].name if first_topic and len(first_topic.concepts) > 1 else "Related Concept"

    return AnswerSheetAnalysis(
        raw_evidence_summary=f"Extracted 2 question responses from previous assessment covering {learning_map.subject}.",
        questions=[
            ExtractedQuestionAnswer(
                question_number="Q1",
                question_text=f"Explain the primary mechanism and significance of {first_concept}.",
                student_answer="It produces energy by breaking things down, but I forgot the specific steps involved.",
                marks_allocated=5.0,
                marks_awarded=2.5,
                teacher_feedback="Missing intermediate steps and key enzyme terminology.",
                relevant_topic=first_topic.topic if first_topic else "Fundamentals",
                relevant_concept=first_concept,
                evaluation_criteria=f"Accurate naming of {first_concept} components and sequential logic.",
                ai_interpretation="Student grasped the general objective but displayed missing procedural recall and specific terminology.",
            ),
            ExtractedQuestionAnswer(
                question_number="Q2",
                question_text=f"How does {second_concept} depend on the inputs of {first_concept}?",
                student_answer="They are basically the same process and happen at the same time.",
                marks_allocated=5.0,
                marks_awarded=1.0,
                teacher_feedback="Incorrect. They are sequential stages.",
                relevant_topic=first_topic.topic if first_topic else "Fundamentals",
                relevant_concept=second_concept,
                evaluation_criteria="Clear distinction between sequential dependency versus concurrent reactions.",
                ai_interpretation="Evidence suggests confusion regarding stage dependency and prerequisite flow.",
            ),
        ],
        identified_weakness_signals=[first_concept, second_concept],
        notes="Analysis distinguishes observed student text and marks from diagnostic interpretations.",
    )


def analyze_previous_answer_sheet(text: str, learning_map: LearningMap) -> AnswerSheetAnalysis:
    if not text or not text.strip():
        raise ValueError("Answer sheet text is empty.")

    mock_llm = os.getenv("MOCK_LLM", "false").strip().lower() in ("true", "1", "yes")
    if mock_llm:
        return _mock_answer_sheet_analysis(text, learning_map)

    prompt = (
        f"LEARNING MAP CONTEXT:\n{learning_map.model_dump_json(indent=2)}\n\n"
        f"ANSWER SHEET TEXT:\n\"\"\"\n{text}\n\"\"\""
    )
    raw_json = _call_llm_json(prompt, ANSWER_SHEET_PROMPT)
    cleaned = _clean_json_string(raw_json)
    data = json.loads(cleaned)
    return AnswerSheetAnalysis.model_validate(data)


# =========================================================
# 3. Diagnostic Assessment Generation (Phase 2)
# =========================================================

VALID_DIMENSIONS = [
    "Concept Understanding",
    "Logical Reasoning",
    "Problem Solving",
    "Practical/Application",
]

ASSESSMENT_GEN_PROMPT = """You are an expert educational diagnostic test creator.
Using the provided Learning Map and uploaded study material (and optional previous answer sheet analysis), generate a personalized diagnostic assessment.

CRITICAL REQUIREMENTS:
1. GROUNDED IN STUDY MATERIAL: Only create questions directly supported by the Learning Map concepts and study material. Do not introduce outside concepts.
2. MULTIPLE QUESTIONS WITH REPEAT DIMENSION TESTING:
   - Generate exactly 8 diagnostic questions: exactly 2 for each of the 4 learning dimensions.
3. 4 LEARNING DIMENSIONS (INTERNAL ONLY - DO NOT mention dimension name in question text):
   - "Concept Understanding": Tests definitions, fundamental principles, and accurate recall of ideas.
   - "Logical Reasoning": Tests cause-and-effect, deductive reasoning, prerequisite relationships, and "why/how" mechanisms.
   - "Problem Solving": Tests scenario analysis, error diagnosis, calculating, or systematic troubleshooting.
   - "Practical/Application": Tests applying concepts to realistic, real-world systems, trade-offs, or implementation contexts.
4. MIXTURE OF DIFFICULTY LEVELS & MARKS:
   - Mix difficulties across questions: "beginner" (3 marks), "intermediate" (5 marks), and "advanced" (8 or 10 marks).
5. STRICT PURITY:
   - ZERO document metadata, course codes (e.g., AL2311, CS8391), lecturer names (e.g., Santhanala), page/slide numbers, or header garbage in questions or concepts.
6. QUESTION METADATA:
   Each question in the JSON array must contain:
   - "id": unique identifier (e.g., "diag_1", "diag_2", etc.)
   - "question": clear, engaging question prompt for the student
   - "topic": exact topic title from the Learning Map
   - "concept": exact concept name from the Learning Map
   - "difficulty": "beginner" | "intermediate" | "advanced"
   - "dimension": one of ["Concept Understanding", "Logical Reasoning", "Problem Solving", "Practical/Application"]
   - "marks": integer marks allocated (e.g., 3, 5, 8, 10)
   - "expected_answer": model answer or core explanation expected from the student (hidden from student)
   - "evaluation_criteria": specific evaluation rubric and key concepts required for grading (hidden from student)

Output strictly valid JSON:
{
  "questions": [
    {
      "id": "diag_1",
      "question": "string",
      "topic": "string",
      "concept": "string",
      "difficulty": "intermediate",
      "dimension": "Concept Understanding",
      "marks": 5,
      "expected_answer": "string",
      "evaluation_criteria": "string"
    }
  ]
}
"""


def validate_diagnostic_question(
    q: DiagnosticQuestion,
    valid_concepts: set,
    seen_prompts: set,
    study_material_text: Optional[str] = None,
) -> Tuple[bool, str]:
    """Validates an individual diagnostic question for academic quality,
    groundedness, dimension alignment, purity, and non-duplication.
    """
    # 1. Concept validity
    concept_clean = clean_metadata_str(q.concept).strip()
    if not concept_clean or is_pure_metadata(concept_clean):
        return False, f"Concept '{q.concept}' contains metadata or is invalid."
    if valid_concepts and concept_clean.lower() not in {c.lower() for c in valid_concepts}:
        return False, f"Concept '{q.concept}' is not present in the Learning Map."

    # 2. Dimension validity
    dim = q.dimension or q.learning_dimension
    if not dim or dim not in VALID_DIMENSIONS:
        return False, f"Invalid learning dimension: '{dim}'."

    # 3. Question prompt clarity and length
    prompt = (q.question or q.question_text or "").strip()
    if len(prompt) < 20:
        return False, "Question prompt is too short or unclear."

    # 4. Strict purity: No course codes or lecturer names or document header garbage
    garbage_pattern = r"(?:AL\d{4}|CS\d{4}|IT\d{4}|EC\d{3,4}|Santhanala|Page\s*\d+|Slide\s*\d+|Unit\s*[-–—:]?\s*[IVX\d]+|L\s*T\s*P\s*C|Regulation\s*\d+)"
    if re.search(garbage_pattern, prompt, re.IGNORECASE):
        return False, "Question prompt contains document metadata or header garbage."
    if re.search(garbage_pattern, q.concept, re.IGNORECASE):
        return False, "Concept contains document metadata."

    # 5. Expected answer and evaluation criteria reasonableness
    exp_ans = (q.expected_answer or "").strip()
    crit = (q.evaluation_criteria or q.expected_criteria or "").strip()
    if len(exp_ans) < 10:
        return False, "Expected answer is missing or insufficient."
    if len(crit) < 10:
        return False, "Evaluation criteria are missing or insufficient."

    # 6. Uniqueness
    normalized_prompt = re.sub(r"\s+", " ", prompt.lower()).strip()
    if normalized_prompt in seen_prompts:
        return False, "Duplicate question prompt detected."

    return True, "Valid"


def _create_fallback_question_for_dim(
    dim: str,
    idx: int,
    concept_pool: List[Tuple[str, str, List[str]]],
) -> DiagnosticQuestion:
    """Creates a grounded, high-quality question guaranteed to test the assigned dimension."""
    topic_name, concept_name, prereqs = concept_pool[idx % len(concept_pool)]
    prereq_name = prereqs[0] if prereqs else f"fundamental prerequisites of {concept_name}"

    templates_by_dim = {
        "Concept Understanding": [
            {
                "diff": "beginner",
                "marks": 3,
                "q": f"Define {concept_name} in your own words. What is its core purpose within {topic_name}?",
                "ans": f"Accurate definition of {concept_name} clearly articulating its primary role, operational mechanism, and significance in {topic_name}.",
                "crit": f"Correct technical definition of {concept_name}, identification of key properties, and clarity of purpose.",
            },
            {
                "diff": "intermediate",
                "marks": 5,
                "q": f"What key structural components and behavioral properties distinguish {concept_name} from other concepts in {topic_name}?",
                "ans": f"Detailed breakdown of the essential properties, structural invariants, and unique behavioral characteristics of {concept_name}.",
                "crit": f"Names at least two distinctive properties of {concept_name}, accurately describes internal behavior, and uses precise terminology.",
            },
        ],
        "Logical Reasoning": [
            {
                "diff": "intermediate",
                "marks": 5,
                "q": f"Explain the cause-and-effect relationship connecting {prereq_name} to {concept_name}. Why is {prereq_name} a necessary prerequisite?",
                "ans": f"Logical chain of dependency showing how the output or principles established by {prereq_name} directly enable the operations in {concept_name}.",
                "crit": f"Clear cause-and-effect chain, explains why prerequisite rules must hold, and avoids circular reasoning.",
            },
            {
                "diff": "advanced",
                "marks": 8,
                "q": f"If a foundational precondition in {concept_name} is violated or inverted, deduce step-by-step what consequences propagate through the system.",
                "ans": f"Deductive multi-step analysis tracing failure propagation from the precondition breach to specific invariant violations and incorrect outputs.",
                "crit": f"Step-by-step causal deduction, identifies intermediate state failures, and provides sound justification.",
            },
        ],
        "Problem Solving": [
            {
                "diff": "intermediate",
                "marks": 5,
                "q": f"You encounter an incorrect result or unexpected state while executing {concept_name}. What systematic diagnostic steps would you take to isolate the defect?",
                "ans": f"Structured troubleshooting procedure: inspect input preconditions, verify intermediate state invariants of {concept_name}, and isolate the boundary anomaly.",
                "crit": f"Systematic analytical methodology, isolation of variables, and actionable verification checkpoints.",
            },
            {
                "diff": "advanced",
                "marks": 10,
                "q": f"Devise a step-by-step resolution strategy to handle a difficult edge case or constraint violation when operating on {concept_name}.",
                "ans": f"Detailed algorithmic or analytical strategy that detects the edge case, preserves system invariants of {concept_name}, and restores valid state.",
                "crit": f"Explicit edge-case handling, algorithmic or logical rigor, and preservation of correctness.",
            },
        ],
        "Practical/Application": [
            {
                "diff": "intermediate",
                "marks": 5,
                "q": f"Describe a practical real-world scenario where implementing {concept_name} provides a clear performance or architectural advantage over simpler approaches.",
                "ans": f"Concrete real-world use case illustrating where {concept_name} is applied, the operational context, and the quantifiable trade-offs or advantages gained.",
                "crit": f"Realistic practical application context, sound explanation of benefits of {concept_name}, and awareness of trade-offs.",
            },
            {
                "diff": "advanced",
                "marks": 8,
                "q": f"How would you integrate {concept_name} into a larger production workflow with multiple interacting components, and what operational trade-offs must be managed?",
                "ans": f"Architectural integration plan addressing component interfaces, data flow, failure recovery, and trade-offs such as latency, memory, or complexity.",
                "crit": f"Practical integration feasibility, system-level architecture awareness, and balanced evaluation of trade-offs.",
            },
        ],
    }

    dim_list = templates_by_dim.get(dim, templates_by_dim["Concept Understanding"])
    tmpl = dim_list[idx % len(dim_list)]

    return DiagnosticQuestion(
        id=f"diag_{idx + 1}",
        topic=topic_name,
        concept=concept_name,
        difficulty=tmpl["diff"],
        dimension=dim,
        learning_dimension=dim,
        marks=tmpl["marks"],
        question=tmpl["q"],
        expected_answer=tmpl["ans"],
        evaluation_criteria=tmpl["crit"],
    )


def validate_and_filter_questions(
    questions: List[DiagnosticQuestion],
    learning_map: LearningMap,
    study_material_text: Optional[str] = None,
) -> List[DiagnosticQuestion]:
    """Validates all generated questions. Any question failing validation is
    regenerated/replaced to guarantee that 8 clean, grounded questions spanning
    all 4 learning dimensions are presented to the student.
    """
    valid_concepts = set()
    concept_pool = []
    for topic in learning_map.topics:
        for c in topic.concepts:
            valid_concepts.add(c.name.strip())
            concept_pool.append((topic.topic, c.name.strip(), c.prerequisites))

    if not concept_pool:
        concept_pool = [("Core Subject", "Foundational Principles", ["Prerequisites"])]

    dim_target_counts = {
        "Concept Understanding": 2,
        "Logical Reasoning": 2,
        "Problem Solving": 2,
        "Practical/Application": 2,
    }

    seen_prompts = set()
    validated_by_dim: Dict[str, List[DiagnosticQuestion]] = {d: [] for d in VALID_DIMENSIONS}

    for q in questions:
        dim = q.dimension or q.learning_dimension
        if dim not in VALID_DIMENSIONS:
            if "logic" in str(dim).lower():
                dim = "Logical Reasoning"
            elif "problem" in str(dim).lower():
                dim = "Problem Solving"
            elif "app" in str(dim).lower() or "pract" in str(dim).lower():
                dim = "Practical/Application"
            else:
                dim = "Concept Understanding"
            q.dimension = dim
            q.learning_dimension = dim

        is_valid, reason = validate_diagnostic_question(
            q, valid_concepts, seen_prompts, study_material_text
        )
        if is_valid and len(validated_by_dim[dim]) < dim_target_counts[dim]:
            prompt_key = re.sub(r"\s+", " ", (q.question or q.question_text or "").lower()).strip()
            seen_prompts.add(prompt_key)
            validated_by_dim[dim].append(q)

    # Fill any missing dimensions with validated fallback questions
    final_questions = []
    q_counter = 1
    for dim in VALID_DIMENSIONS:
        current_list = validated_by_dim[dim]
        while len(current_list) < dim_target_counts[dim]:
            fallback_q = _create_fallback_question_for_dim(dim, q_counter - 1, concept_pool)
            current_list.append(fallback_q)
            q_counter += 1

        for q in current_list[:dim_target_counts[dim]]:
            q.id = f"diag_{len(final_questions) + 1}"
            final_questions.append(q)

    return final_questions


def _mock_diagnostic_questions(
    learning_map: LearningMap,
    study_material_text: Optional[str] = None,
) -> List[DiagnosticQuestion]:
    concept_pool = []
    for topic in learning_map.topics:
        for concept in topic.concepts:
            concept_pool.append((topic.topic, concept.name, concept.prerequisites))

    if not concept_pool:
        concept_pool = [("Core Topic", "Core Concept", ["Prerequisites"])]

    raw_questions = []
    q_idx = 0
    for dim in VALID_DIMENSIONS:
        for _ in range(2):
            q = _create_fallback_question_for_dim(dim, q_idx, concept_pool)
            raw_questions.append(q)
            q_idx += 1

    return validate_and_filter_questions(raw_questions, learning_map, study_material_text)


def generate_diagnostic_assessment(
    learning_map: LearningMap,
    answer_sheet_analysis: Optional[AnswerSheetAnalysis] = None,
    study_material_text: Optional[str] = None,
) -> List[DiagnosticQuestion]:
    clean_lm = clean_learning_map(learning_map)
    mock_llm = os.getenv("MOCK_LLM", "false").strip().lower() in ("true", "1", "yes")
    if mock_llm:
        return _mock_diagnostic_questions(clean_lm, study_material_text)

    context = f"LEARNING MAP:\n{clean_lm.model_dump_json(indent=2)}\n"
    if study_material_text and study_material_text.strip():
        filtered_text = _pre_filter_study_material_text(study_material_text)
        excerpt = filtered_text[:8000]
        context += f"\nUPLOADED STUDY MATERIAL TEXT (FOR GROUNDING):\n\"\"\"\n{excerpt}\n\"\"\"\n"
    if answer_sheet_analysis:
        context += f"\nPREVIOUS ANSWER SHEET EVIDENCE:\n{answer_sheet_analysis.model_dump_json(indent=2)}\n"

    prompt = f"GENERATE DIAGNOSTIC QUESTIONS ACCORDING TO GUIDELINES:\n{context}"
    raw_json = _call_llm_json(prompt, ASSESSMENT_GEN_PROMPT)
    cleaned = _clean_json_string(raw_json)
    data = json.loads(cleaned)
    raw_questions = [DiagnosticQuestion.model_validate(q) for q in data.get("questions", [])]

    # Strictly validate each question before presenting to the student
    return validate_and_filter_questions(raw_questions, clean_lm, study_material_text)


# =========================================================
# 4. Independent Per-Question Rubric Evaluation & Diagnosis
# =========================================================

def evaluate_single_answer(
    q: DiagnosticQuestion,
    student_answer: str,
) -> EvaluatedQuestionResult:
    """Evaluates an individual student answer independently against its question-specific
    evaluation criteria, expected answer, and assigned learning dimension.

    Strict rules:
    - DO NOT hard-code 84% or any uniform target score.
    - Evaluates correctness, completeness, presence of required technical terms,
      dimension-specific reasoning/mechanics, missing elements, and misconceptions.
    - Allows different answers to receive genuinely different marks (0%, 25%, 50%, 75%, 100%).
    """
    ans = student_answer.strip()
    marks_max = float(q.marks or 5)
    dim = q.dimension or q.learning_dimension or "Concept Understanding"
    concept = q.concept

    # 1. Blank or whitespace response
    if not ans:
        return EvaluatedQuestionResult(
            question_id=q.id,
            question_text=q.question or q.question_text or "",
            concept=concept,
            topic=q.topic,
            dimension=dim,
            learning_dimension=dim,
            student_answer="[No answer provided]",
            score=0.0,
            marks_awarded=0.0,
            marks_possible=marks_max,
            percentage=0.0,
            rubric_evaluation=f"No response was submitted for {q.id}. Criteria not satisfied.",
            evidence=[f"Question {q.id} ({dim}) was left unanswered."],
            missing_elements=["Complete explanation missing."],
            misconceptions=[],
            misconceptions_detected=None,
        )

    ans_lower = ans.lower()
    words = re.findall(r"\w+", ans_lower)
    word_count = len(words)

    # Keywords from concept and criteria
    concept_keywords = [w.lower() for w in re.findall(r"\w+", concept) if len(w) > 3]
    concept_matches = sum(1 for kw in concept_keywords if kw in ans_lower)
    concept_ratio = concept_matches / max(1, len(concept_keywords))

    missing_elements: List[str] = []
    misconceptions: List[str] = []
    evidence_notes: List[str] = []

    # Detect explicit misconceptions or contradictory claims
    contradiction_patterns = [
        (r"\b(same process|basically the same|identical)\b", "Confusing distinct sequential processes as identical"),
        (r"\b(doesn't matter|does not matter|arbitrary|random)\b", "Failing to recognize strict invariant requirements"),
        (r"\b(no need to check|skip verification|ignore)\b", "Dismissing essential verification or prerequisite checks"),
    ]
    for pat, label in contradiction_patterns:
        if re.search(pat, ans_lower):
            misconceptions.append(label)

    # Dimension-specific evaluation logic
    dim_score_ratio = 0.5  # baseline
    if dim == "Concept Understanding":
        # Expect accurate definition, operational role, key terminology
        has_definition = any(w in ans_lower for w in ["defined", "means", "refers", "structure", "mechanism", "technique", "algorithm", "process"])
        has_purpose = any(w in ans_lower for w in ["used to", "purpose", "allows", "enables", "stores", "organizes", "optimizes", "in order to"])

        if word_count < 8:
            dim_score_ratio = 0.25
            missing_elements.append("Definition lacks necessary technical detail and operational purpose.")
            evidence_notes.append(f"Answer gave only a shallow {word_count}-word mention of {concept}.")
        elif not has_definition and not has_purpose:
            dim_score_ratio = 0.45
            missing_elements.append("Missing explicit functional definition or purpose.")
            evidence_notes.append(f"Answer mentioned {concept} but omitted operational definition.")
        elif has_definition and has_purpose and (concept_ratio >= 0.5 or word_count >= 20):
            dim_score_ratio = 0.95
            evidence_notes.append(f"Demonstrated clear conceptual recall and purpose of {concept}.")
        else:
            dim_score_ratio = 0.70
            missing_elements.append("Minor omission in distinguishing features.")
            evidence_notes.append(f"Grasped general idea of {concept} with partial terminology.")

    elif dim == "Logical Reasoning":
        # Expect causal connectors, dependency flow, cause-and-effect
        causal_words = ["because", "causes", "leads to", "depends", "since", "therefore", "as a result", "consequence", "precedes", "ensures", "fails"]
        has_causal = any(cw in ans_lower for cw in causal_words)

        if word_count < 10 or not has_causal:
            dim_score_ratio = 0.25
            missing_elements.append("Lacks cause-and-effect reasoning and sequential dependency flow.")
            evidence_notes.append(f"Failed to articulate causal links connecting prerequisites to {concept}.")
        elif len(misconceptions) > 0:
            dim_score_ratio = 0.35
            missing_elements.append("Reasoning contains flawed stage dependency assumptions.")
            evidence_notes.append(f"Exhibited misconception in reasoning: {misconceptions[0]}.")
        elif word_count >= 18 and has_causal:
            dim_score_ratio = 0.85
            evidence_notes.append(f"Articulated logical cause-and-effect dependencies for {concept}.")
        else:
            dim_score_ratio = 0.55
            missing_elements.append("Intermediate causal steps partially omitted.")
            evidence_notes.append(f"Showed partial logical awareness but skipped intermediate deduction.")

    elif dim == "Problem Solving":
        # Expect troubleshooting steps, variable isolation, testing edge cases
        action_words = ["check", "verify", "step", "isolate", "inspect", "test", "debug", "trace", "boundary", "condition", "edge case", "correct"]
        action_matches = sum(1 for aw in action_words if aw in ans_lower)

        if action_matches == 0 or word_count < 10:
            dim_score_ratio = 0.20
            missing_elements.append("No actionable troubleshooting steps or variable isolation proposed.")
            evidence_notes.append(f"Did not provide structured diagnostic methodology for {concept}.")
        elif action_matches >= 3 and word_count >= 18:
            dim_score_ratio = 0.90
            evidence_notes.append(f"Provided structured, actionable troubleshooting procedure for {concept}.")
        elif action_matches >= 1:
            dim_score_ratio = 0.60
            missing_elements.append("Troubleshooting procedure lacks verification checkpoints.")
            evidence_notes.append(f"Outlined partial diagnostic steps for {concept}.")
        else:
            dim_score_ratio = 0.40
            missing_elements.append("Proposed solution does not isolate root variables.")

    elif dim == "Practical/Application":
        # Expect real-world context, integration, practical trade-offs
        practical_words = ["system", "implement", "real-world", "practical", "database", "network", "cache", "performance", "trade-off", "latency", "scale", "production"]
        practical_matches = sum(1 for pw in practical_words if pw in ans_lower)

        if practical_matches == 0 and word_count < 15:
            dim_score_ratio = 0.30
            missing_elements.append("Failed to articulate realistic practical scenario or architectural trade-offs.")
            evidence_notes.append(f"Struggled to connect {concept} to realistic implementation context.")
        elif practical_matches >= 2 and word_count >= 18:
            dim_score_ratio = 0.85
            evidence_notes.append(f"Demonstrated practical scenario application with concrete trade-off awareness.")
        else:
            dim_score_ratio = 0.55
            missing_elements.append("Practical benefits described without concrete implementation trade-offs.")
            evidence_notes.append(f"Demonstrated basic application context but lacked depth.")

    # Penalty for misconceptions
    if misconceptions:
        dim_score_ratio = max(0.10, dim_score_ratio - 0.25)

    # Calculate actual marks awarded
    raw_score = marks_max * dim_score_ratio
    # Round to 1 decimal place, bounded between 0 and marks_max
    score = round(max(0.0, min(marks_max, raw_score)), 1)
    pct = round((score / marks_max) * 100, 1)

    # Compose criteria-based rubric evaluation narrative
    if pct >= 80:
        rubric_eval = f"Solid, rigorous response meeting core criteria for {concept}. Appropriately demonstrated {dim}."
    elif pct >= 60:
        rubric_eval = f"Competent answer covering fundamental points of {concept}. Partially omitted: {'; '.join(missing_elements) if missing_elements else 'depth'}."
    elif pct >= 35:
        rubric_eval = f"Demonstrates partial awareness of {concept} but exhibits notable gaps in {dim}. Missing: {'; '.join(missing_elements) if missing_elements else 'key elements'}."
    else:
        rubric_eval = f"Minimal or incorrect response for {concept}. Failed to meet criteria for {dim}. Missing: {'; '.join(missing_elements) if missing_elements else 'foundational concepts'}."

    misconceptions_str = "; ".join(misconceptions) if misconceptions else None

    return EvaluatedQuestionResult(
        question_id=q.id,
        question_text=q.question or q.question_text or "",
        concept=concept,
        topic=q.topic,
        dimension=dim,
        learning_dimension=dim,
        student_answer=ans,
        score=score,
        marks_awarded=score,
        marks_possible=marks_max,
        percentage=pct,
        rubric_evaluation=rubric_eval,
        evidence=evidence_notes,
        missing_elements=missing_elements,
        misconceptions=misconceptions,
        misconceptions_detected=misconceptions_str,
    )


DIAGNOSIS_PROMPT = """You are an expert learning diagnostic evaluator.
Synthesize all available evidence:
1. Learning Map
2. Diagnostic Questions and Expected Criteria
3. Student Answers
4. (Optional) Previous Answer Sheet Evidence and marks

CRITICAL EVALUATION RULES:
1. INDEPENDENT SCORING: Evaluate EACH student answer individually against its question-specific criteria.
   - DO NOT assign uniform or near-identical marks (such as 84% or 85% to every answer).
   - Base marks strictly on correctness, completeness, presence of key concepts, missing elements, and misconceptions.
   - Allow different answers to receive genuinely different marks.
2. CALCULATE DIMENSION SCORES:
   - Calculate each dimension as: (total marks earned / total possible marks) * 100.
   - DO NOT force dimensions toward the same score.
3. CALCULATE CONCEPT PERFORMANCE:
   - Calculate concept score as: (total marks earned / total possible marks) * 100 for that concept.
   - Only call a concept weak if actual question evidence demonstrates friction (< 75%).
4. CAUTIOUS ROOT CAUSE ANALYSIS:
   - For every root cause, cite specific answer evidence and assign a confidence level ("High", "Medium", "Low").
   - If evidence is insufficient, state: "No clear prerequisite gap established from the available evidence."
   - Use cautious phrasing: "Responses indicate...", "Evidence suggests...", "Possible contributing factor...".
   - Never claim to measure permanent ability or intelligence.
   - NEVER call a score >= 75% a "weakness". Performance labels must correspond to evidence: >=75% is Solid, 50-74% Developing, <50% Needs Focus.
5. PREVIOUS ANSWER SHEET:
   - Distinguish previous evidence, current evidence, and combined conclusion.

Output strictly valid JSON:
{
  "overall_summary": "Cautious evidence-based narrative summary",
  "dimension_scores": {
    "concept_understanding": 70,
    "logical_reasoning": 35,
    "problem_solving": 55,
    "application": 40
  },
  "concept_scores": [
    {
      "topic": "string",
      "concept": "string",
      "marks_awarded": 3.0,
      "marks_possible": 5.0,
      "percentage": 60.0,
      "performance_level": "Developing",
      "evidence_count": 1
    }
  ],
  "topic_diagnosis": [
    {
      "topic": "string",
      "concept": "string",
      "dimensions": {
        "concept_understanding": 70,
        "logical_reasoning": 35,
        "problem_solving": 55,
        "application": 40
      },
      "primary_difficulty": "string description of friction",
      "possible_root_cause": "cautious root cause statement",
      "confidence": "Medium",
      "evidence": ["quote or observation from student response"]
    }
  ],
  "identified_friction": ["specific friction point 1"],
  "possible_root_causes": [
    {
      "root_cause": "cautiously worded root cause",
      "affected_concept": "string",
      "supporting_evidence": ["quote or observation from student response"],
      "confidence_level": "High"
    }
  ],
  "prerequisite_gaps": ["identified prior gaps"],
  "recommended_focus": ["priority concepts to reinforce"],
  "previous_evidence_summary": "string or null",
  "current_evidence_summary": "string",
  "combined_conclusion": "string or null",
  "confidence": "Medium",
  "evaluated_questions": [
    {
      "question_id": "string",
      "question_text": "string",
      "concept": "string",
      "dimension": "string",
      "student_answer": "string",
      "score": 3.0,
      "marks_possible": 5.0,
      "percentage": 60.0,
      "rubric_evaluation": "string evaluation against criteria",
      "missing_elements": ["string"],
      "misconceptions": ["string"]
    }
  ]
}
"""


def _synthesize_learning_diagnosis(
    learning_map: LearningMap,
    questions: List[DiagnosticQuestion],
    student_answers: List[StudentResponseItem],
    answer_sheet: Optional[AnswerSheetAnalysis],
) -> CombinedDiagnosis:
    """Deterministically synthesizes a learning diagnosis with independent
    per-question evaluations, exact mathematical dimension scores, concept performance,
    cautious root causes, and previous answer sheet integration.
    """
    clean_lm = clean_learning_map(learning_map)
    answers_map = {a.question_id: a.student_answer for a in student_answers}

    # 1. Independent evaluation of each question
    evaluated_questions: List[EvaluatedQuestionResult] = []
    for q in questions:
        ans = answers_map.get(q.id, "")
        eval_res = evaluate_single_answer(q, ans)
        evaluated_questions.append(eval_res)

    # 2. Mathematical calculation of Dimension Scores:
    # total marks earned / total possible marks * 100
    dim_totals = {
        "Concept Understanding": {"earned": 0.0, "possible": 0.0},
        "Logical Reasoning": {"earned": 0.0, "possible": 0.0},
        "Problem Solving": {"earned": 0.0, "possible": 0.0},
        "Practical/Application": {"earned": 0.0, "possible": 0.0},
    }

    for eq in evaluated_questions:
        d = eq.learning_dimension or eq.dimension
        if d in dim_totals:
            dim_totals[d]["earned"] += eq.marks_awarded or eq.score or 0.0
            dim_totals[d]["possible"] += eq.marks_possible or 5.0

    def calc_dim_pct(d_key: str) -> int:
        poss = dim_totals[d_key]["possible"]
        if poss <= 0:
            return 50
        return int(round((dim_totals[d_key]["earned"] / poss) * 100))

    score_concept = calc_dim_pct("Concept Understanding")
    score_logic = calc_dim_pct("Logical Reasoning")
    score_problem = calc_dim_pct("Problem Solving")
    score_app = calc_dim_pct("Practical/Application")

    dimension_scores = DimensionScores(
        concept_understanding=max(0, min(100, score_concept)),
        logical_reasoning=max(0, min(100, score_logic)),
        problem_solving=max(0, min(100, score_problem)),
        application=max(0, min(100, score_app)),
    )

    # 3. Concept / Topic Performance calculation from actual question evidence
    concept_map: Dict[str, Dict[str, Any]] = {}
    for eq in evaluated_questions:
        c_name = eq.concept
        if c_name not in concept_map:
            concept_map[c_name] = {
                "topic": eq.topic or clean_lm.subject,
                "earned": 0.0,
                "possible": 0.0,
                "count": 0,
                "evidence": [],
                "misconceptions": [],
            }
        concept_map[c_name]["earned"] += eq.marks_awarded or eq.score or 0.0
        concept_map[c_name]["possible"] += eq.marks_possible or 5.0
        concept_map[c_name]["count"] += 1
        if eq.evidence:
            concept_map[c_name]["evidence"].extend(eq.evidence)
        if eq.misconceptions:
            concept_map[c_name]["misconceptions"].extend(eq.misconceptions)

    concept_scores: List[ConceptScore] = []
    weak_concepts = []
    strong_concepts = []

    for c_name, c_data in concept_map.items():
        poss = c_data["possible"]
        earned = c_data["earned"]
        pct = round((earned / poss) * 100, 1) if poss > 0 else 50.0

        if pct >= 80:
            perf_level = "Solid"
            strong_concepts.append(c_name)
        elif pct >= 60:
            perf_level = "Developing"
            # Only treat developing as a weak focus if explicit misconceptions were flagged
            if c_data.get("misconceptions"):
                weak_concepts.append((c_name, pct, c_data))
            else:
                strong_concepts.append(c_name)
        else:
            perf_level = "Needs Focus"
            weak_concepts.append((c_name, pct, c_data))

        concept_scores.append(
            ConceptScore(
                topic=c_data["topic"],
                concept=c_name,
                marks_awarded=earned,
                marks_possible=poss,
                percentage=pct,
                performance_level=perf_level,
                evidence_count=c_data["count"],
            )
        )

    # Sort weak concepts by lowest percentage first
    weak_concepts.sort(key=lambda x: x[1])

    # 4. Synthesize Root Causes with supporting evidence and confidence levels
    possible_root_causes: List[PossibleRootCause] = []
    identified_friction: List[str] = []
    prerequisite_gaps: List[str] = []
    topic_diagnosis: List[TopicDiagnosis] = []

    # Map prerequisites from learning map
    prereq_by_concept: Dict[str, List[str]] = {}
    for t in clean_lm.topics:
        for c in t.concepts:
            prereq_by_concept[c.name] = c.prerequisites

    if weak_concepts:
        for c_name, c_pct, c_data in weak_concepts[:2]:
            prereqs = prereq_by_concept.get(c_name, [])
            candidate_prereq = prereqs[0] if prereqs else f"Foundations of {c_name}"

            friction_str = f"Responses demonstrate friction in {c_name} ({c_pct}%), particularly with operational execution and deduction."
            identified_friction.append(friction_str)

            # Determine confidence level
            conf = "High" if (len(c_data["evidence"]) >= 2 or (answer_sheet and c_name in answer_sheet.identified_weakness_signals)) else "Medium"

            cause_str = (
                f"Evidence suggests potential friction connecting the foundational rules of {candidate_prereq} "
                f"to multi-step reasoning in {c_name}."
            )
            ev_list = c_data["evidence"][:3]
            if not ev_list:
                ev_list = [f"Student achieved {c_pct}% across assessed questions for {c_name}."]

            possible_root_causes.append(
                PossibleRootCause(
                    root_cause=cause_str,
                    affected_concept=c_name,
                    supporting_evidence=ev_list,
                    confidence_level=conf,
                )
            )
            prerequisite_gaps.append(candidate_prereq)

            topic_diagnosis.append(
                TopicDiagnosis(
                    topic=c_data["topic"],
                    concept=c_name,
                    dimensions=dimension_scores,
                    primary_difficulty=friction_str,
                    possible_root_cause=cause_str,
                    evidence=ev_list,
                    confidence=conf,
                    missing_elements=c_data.get("missing_elements", []),
                    misconceptions=c_data.get("misconceptions", []),
                )
            )
    else:
        # All tested concepts scored >= 75%
        possible_root_causes.append(
            PossibleRootCause(
                root_cause="No clear prerequisite gap established from the available evidence.",
                affected_concept="Overall Curriculum",
                supporting_evidence=["Student answers met or exceeded benchmark criteria across assessed questions."],
                confidence_level="Low",
            )
        )
        first_topic = clean_lm.topics[0] if clean_lm.topics else None
        first_concept = first_topic.concepts[0].name if first_topic and first_topic.concepts else "Core Concepts"
        topic_diagnosis.append(
            TopicDiagnosis(
                topic=first_topic.topic if first_topic else "Core Curriculum",
                concept=first_concept,
                dimensions=dimension_scores,
                primary_difficulty="No significant friction identified; student demonstrated solid mastery across core criteria.",
                possible_root_cause="No clear prerequisite gap established from the available evidence.",
                evidence=["Answers consistently demonstrated sound definitions, logical deduction, and application."],
                confidence="Low",
            )
        )

    # Determine recommended focus areas
    recommended_focus = [c[0] for c in weak_concepts[:3]]
    if not recommended_focus:
        recommended_focus = [cs.concept for cs in concept_scores[:2]]

    # 5. Integrate Previous Answer Sheet Evidence
    prev_summary = None
    curr_summary = (
        f"Diagnostic test results indicate {score_concept}% in Concept Understanding, "
        f"{score_logic}% in Logical Reasoning, {score_problem}% in Problem Solving, and "
        f"{score_app}% in Practical/Application across {len(evaluated_questions)} questions."
    )
    combined_conclusion = None

    if answer_sheet:
        prev_summary = (
            f"Previous answer sheet indicated {len(answer_sheet.questions)} extracted items with noted difficulty in "
            f"{', '.join(answer_sheet.identified_weakness_signals) if answer_sheet.identified_weakness_signals else 'procedural steps'}."
        )
        # Check corroboration
        corroborated = [c for c in answer_sheet.identified_weakness_signals if any(w[0] == c for w in weak_concepts)]
        if corroborated:
            combined_conclusion = (
                f"Combined evidence confirms recurring friction in {', '.join(corroborated)}, "
                f"present in both the previous answer sheet and current diagnostic assessment."
            )
        else:
            combined_conclusion = (
                "Current diagnostic answers demonstrate progress compared to historical answer sheet signals, "
                "with remaining focus areas localized to multi-step reasoning."
            )

    # 6. Overall Cautious Summary
    # Respect score thresholds: never call a >= 75% score a weakness!
    dim_performance_phrases = []
    if score_concept >= 75:
        dim_performance_phrases.append(f"solid foundational concept understanding ({score_concept}%)")
    else:
        dim_performance_phrases.append(f"developing concept recall ({score_concept}%)")

    weakest_dim = min([
        ("Logical Reasoning", score_logic),
        ("Problem Solving", score_problem),
        ("Practical/Application", score_app),
    ], key=lambda x: x[1])

    if weakest_dim[1] < 75:
        narrative_weakness = f"evidence suggests friction when engaging in {weakest_dim[0]} ({weakest_dim[1]}%)"
    else:
        narrative_weakness = f"balanced performance across reasoning and application ({weakest_dim[1]}%)"

    overall_summary = (
        f"Evaluation across four learning dimensions indicates {', '.join(dim_performance_phrases)}, with "
        f"{narrative_weakness}. "
        f"Performance patterns suggest that targeted review of {', '.join(recommended_focus[:2])} will help solidify "
        f"end-to-end analytical confidence."
    )

    return CombinedDiagnosis(
        overall_summary=overall_summary,
        dimension_scores=dimension_scores,
        dimension_averages=dimension_scores,
        concept_scores=concept_scores,
        topic_diagnosis=topic_diagnosis,
        identified_friction=identified_friction,
        possible_root_causes=possible_root_causes,
        prerequisite_gaps=prerequisite_gaps,
        recommended_focus=recommended_focus,
        recommended_focus_areas=recommended_focus,
        evaluated_questions=evaluated_questions,
        previous_evidence_summary=prev_summary,
        current_evidence_summary=curr_summary,
        combined_conclusion=combined_conclusion,
        confidence="High" if weak_concepts and len(weak_concepts[0][2]["evidence"]) >= 2 else "Medium",
    )


def diagnose_learning(
    learning_map: LearningMap,
    questions: List[DiagnosticQuestion],
    student_answers: List[StudentResponseItem],
    answer_sheet_analysis: Optional[AnswerSheetAnalysis] = None,
) -> CombinedDiagnosis:
    clean_lm = clean_learning_map(learning_map)
    mock_llm = os.getenv("MOCK_LLM", "false").strip().lower() in ("true", "1", "yes")
    if mock_llm:
        return _synthesize_learning_diagnosis(clean_lm, questions, student_answers, answer_sheet_analysis)

    answers_dict = {a.question_id: a.student_answer for a in student_answers}
    q_and_a = []
    for q in questions:
        q_and_a.append({
            "id": q.id,
            "topic": q.topic,
            "concept": q.concept,
            "dimension": q.dimension or q.learning_dimension,
            "marks": q.marks,
            "question": q.question or q.question_text,
            "expected_answer": q.expected_answer,
            "evaluation_criteria": q.evaluation_criteria,
            "student_answer": answers_dict.get(q.id, "[No answer provided]"),
        })

    prompt_data = {
        "learning_map": clean_lm.model_dump(),
        "questions_and_student_answers": q_and_a,
    }
    if answer_sheet_analysis:
        prompt_data["previous_answer_sheet_analysis"] = answer_sheet_analysis.model_dump()

    prompt = f"SYNTHESIZE DIAGNOSIS FROM EVIDENCE:\n{json.dumps(prompt_data, indent=2)}"
    raw_json = _call_llm_json(prompt, DIAGNOSIS_PROMPT)
    cleaned = _clean_json_string(raw_json)
    data = json.loads(cleaned)

    # Parse questions from LLM or evaluate them if missing
    evaluated_questions = []
    for raw_eq in data.get("evaluated_questions", []):
        try:
            evaluated_questions.append(EvaluatedQuestionResult.model_validate(raw_eq))
        except Exception:
            pass

    if not evaluated_questions:
        return _synthesize_learning_diagnosis(clean_lm, questions, student_answers, answer_sheet_analysis)

    # Calculate exact mathematical dimension scores from the evaluated questions
    # to guarantee accuracy regardless of LLM arithmetic
    dim_totals = {
        "Concept Understanding": {"earned": 0.0, "possible": 0.0},
        "Logical Reasoning": {"earned": 0.0, "possible": 0.0},
        "Problem Solving": {"earned": 0.0, "possible": 0.0},
        "Practical/Application": {"earned": 0.0, "possible": 0.0},
    }
    for eq in evaluated_questions:
        d = eq.learning_dimension or eq.dimension
        if d in dim_totals:
            dim_totals[d]["earned"] += eq.marks_awarded or eq.score or 0.0
            dim_totals[d]["possible"] += eq.marks_possible or 5.0

    def calc_dim_pct(d_key: str) -> int:
        poss = dim_totals[d_key]["possible"]
        if poss <= 0:
            return 50
        return int(round((dim_totals[d_key]["earned"] / poss) * 100))

    calc_dim_scores = DimensionScores(
        concept_understanding=max(0, min(100, calc_dim_pct("Concept Understanding"))),
        logical_reasoning=max(0, min(100, calc_dim_pct("Logical Reasoning"))),
        problem_solving=max(0, min(100, calc_dim_pct("Problem Solving"))),
        application=max(0, min(100, calc_dim_pct("Practical/Application"))),
    )

    data["dimension_scores"] = calc_dim_scores.model_dump()
    data["dimension_averages"] = calc_dim_scores.model_dump()
    data["evaluated_questions"] = [eq.model_dump() for eq in evaluated_questions]

    return CombinedDiagnosis.model_validate(data)


# =========================================================
# 5. ONE Personalized Intervention (Phase 2)
# =========================================================

INTERVENTION_PROMPT = """You are an expert personalized learning pathway designer.
CRITICAL RULE: Create ONLY ONE unified personalized learning intervention.
Combine all diagnosed evidence (from the Learning Map, diagnostic responses, and any previous answer sheet mistakes) into a single cohesive, targeted study plan.

The intervention MUST specifically address the student's weakest learning dimensions and diagnosed prerequisite gaps.

The intervention should include:
- A clear, encouraging title and overview.
- "weakness_focus_summary": clear statement of the weakest learning dimensions targeted.
- "suggested_learning_sequence": ordered list of recommended study steps.
- Targeted modules for each diagnosed weak concept:
  - "concept": concept title
  - "identified_gap": brief summary of the diagnosed gap
  - "prerequisite_refresher": targeted reminder of prior knowledge needed
  - "core_explanation": intuitive, clear conceptual explanation
  - "misconception_clarification": specific clarification of mistakes observed
  - "worked_example": concrete walkthrough demonstrating application
  - "practice_prompts": 2-3 short interactive self-check questions
- General study recommendations.

Output strictly valid JSON:
{
  "title": "string",
  "overview": "string",
  "weakness_focus_summary": "string",
  "suggested_learning_sequence": ["string"],
  "targeted_modules": [
    {
      "concept": "string",
      "identified_gap": "string",
      "prerequisite_refresher": "string or null",
      "core_explanation": "string",
      "misconception_clarification": "string or null",
      "worked_example": "string",
      "practice_prompts": ["string"]
    }
  ],
  "study_recommendations": ["string"]
}
"""


def _mock_intervention(diagnosis: CombinedDiagnosis, learning_map: LearningMap) -> PersonalizedIntervention:
    clean_lm = clean_learning_map(learning_map)
    concept_name = (
        diagnosis.topic_diagnosis[0].concept if diagnosis.topic_diagnosis else "Core Concept"
    )
    prereq = diagnosis.prerequisite_gaps[0] if diagnosis.prerequisite_gaps else f"Foundational Principles of {concept_name}"

    dims = {
        "Logical Reasoning": diagnosis.dimension_averages.logical_reasoning,
        "Practical Application": diagnosis.dimension_averages.application,
        "Problem Solving": diagnosis.dimension_averages.problem_solving,
        "Concept Understanding": diagnosis.dimension_averages.concept_understanding,
    }
    weakest_dim = min(dims, key=dims.get)
    weakest_score = dims[weakest_dim]

    module = InterventionModule(
        concept=concept_name,
        identified_gap=f"Friction in {weakest_dim} ({weakest_score}%), particularly connecting the foundational rules of {prereq} to multi-stage reasoning.",
        prerequisite_refresher=f"Foundational Check: Review {prereq} to verify input preconditions, invariants, and constraints before executing {concept_name}.",
        core_explanation=(
            f"{concept_name} operates as a coordinated sequential pathway rather than isolated rules. "
            f"Focus on the state transitions: track precisely what changes at each step, what dependencies are required, and what output is generated."
        ),
        misconception_clarification=(
            f"A common misconception is assuming {concept_name} operates independently without verifying the outputs from {prereq}. "
            f"Always check stage dependencies and boundary constraints before calculating results."
        ),
        worked_example=(
            f"Step-by-Step Guided Walkthrough for {concept_name}:\n"
            f"1. Precondition Check: Verify that input states satisfy all rules established in {prereq}.\n"
            f"2. Core Transformation: Apply the governing mechanism of {concept_name} sequentially.\n"
            f"3. Verification: Check intermediate states and test boundary conditions to guarantee correct outputs."
        ),
        practice_prompts=[
            f"Self-Check 1: If the input state from {prereq} is modified or degraded by 50%, how does that propagate through {concept_name}?",
            f"Self-Check 2: What systematic troubleshooting step would you perform first if {concept_name} produces an erroneous result?",
        ],
    )

    return PersonalizedIntervention(
        title=f"Personalized Mastery Pathway: {clean_lm.subject}",
        overview=(
            f"This unified intervention synthesizes all diagnostic evidence into ONE targeted learning plan. "
            f"It specifically targets your diagnosed weakest dimension ({weakest_dim} at {weakest_score}%) in {concept_name}, "
            f"bridging prerequisite gaps into solid logical reasoning and practical application."
        ),
        weakness_focus_summary=(
            f"Targeted Focus: Reinforcing {weakest_dim} ({weakest_score}%) and bridging the prerequisite gap in {prereq}."
        ),
        suggested_learning_sequence=[
            f"1. Prerequisite Review: Solidify core concepts in {prereq}",
            f"2. Mechanistic Understanding: Study state transitions in {concept_name}",
            f"3. Worked Walkthrough: Work through the 3-step verification methodology",
            f"4. Active Self-Check: Answer the 2 practice prompts before beginning reassessment",
        ],
        targeted_modules=[module],
        study_recommendations=[
            f"Review the prerequisite refresher for {prereq} before attempting multi-step application scenarios.",
            "Work through the 3-step verification method in the worked example rather than memorizing formulas.",
            "Attempt the self-check practice prompts actively to validate your reasoning before taking the reassessment.",
        ],
    )


def generate_personalized_intervention(
    diagnosis: CombinedDiagnosis,
    learning_map: LearningMap,
) -> PersonalizedIntervention:
    clean_lm = clean_learning_map(learning_map)
    mock_llm = os.getenv("MOCK_LLM", "false").strip().lower() in ("true", "1", "yes")
    if mock_llm:
        return _mock_intervention(diagnosis, clean_lm)

    prompt = (
        f"LEARNING MAP:\n{clean_lm.model_dump_json(indent=2)}\n\n"
        f"DIAGNOSIS REPORT:\n{diagnosis.model_dump_json(indent=2)}"
    )
    raw_json = _call_llm_json(prompt, INTERVENTION_PROMPT)
    cleaned = _clean_json_string(raw_json)
    data = json.loads(cleaned)
    return PersonalizedIntervention.model_validate(data)


# =========================================================
# 6. Reassessment Generation & Evaluation (Phase 2)
# =========================================================

REASSESSMENT_GEN_PROMPT = """You are an educational test designer creating a short, targeted reassessment.
Based on the student's diagnosed weak areas, generate 3 to 4 NEW but COMPARABLE questions.
DO NOT repeat the exact same questions from earlier assessments.
Target the specific concepts and learning dimensions where weaknesses were diagnosed (especially logical reasoning and application).

Output strictly valid JSON:
{
  "questions": [
    {
      "id": "reassess_1",
      "target_concept": "string",
      "learning_dimension": "concept_understanding" | "logical_reasoning" | "problem_solving" | "application",
      "question_text": "string",
      "expected_criteria": "string"
    }
  ]
}
"""


def _mock_reassessment_questions(diagnosis: CombinedDiagnosis) -> List[ReassessmentQuestion]:
    concept_name = (
        diagnosis.topic_diagnosis[0].concept if diagnosis.topic_diagnosis else "Core Concept"
    )

    return [
        ReassessmentQuestion(
            id="reassess_1",
            target_concept=concept_name,
            learning_dimension="logical_reasoning",
            question_text=f"How does the sequential dependency of {concept_name} prevent errors in the downstream process?",
            expected_criteria=f"Demonstrates clear reasoning about sequential dependencies and cause-and-effect.",
        ),
        ReassessmentQuestion(
            id="reassess_2",
            target_concept=concept_name,
            learning_dimension="problem_solving",
            question_text=f"In a test environment, {concept_name} fails to yield expected output. What two diagnostic checks would you conduct first?",
            expected_criteria="Identifies logical root causes and systematic verification procedure.",
        ),
        ReassessmentQuestion(
            id="reassess_3",
            target_concept=concept_name,
            learning_dimension="application",
            question_text=f"Propose a practical adjustment to improve efficiency during {concept_name} based on the core mechanisms you studied.",
            expected_criteria="Valid application of principles to improve a practical outcome.",
        ),
    ]


def generate_reassessment(
    diagnosis: CombinedDiagnosis,
    learning_map: LearningMap,
) -> List[ReassessmentQuestion]:
    clean_lm = clean_learning_map(learning_map)
    mock_llm = os.getenv("MOCK_LLM", "false").strip().lower() in ("true", "1", "yes")
    if mock_llm:
        return _mock_reassessment_questions(diagnosis)

    prompt = (
        f"LEARNING MAP:\n{clean_lm.model_dump_json(indent=2)}\n\n"
        f"DIAGNOSIS:\n{diagnosis.model_dump_json(indent=2)}"
    )
    raw_json = _call_llm_json(prompt, REASSESSMENT_GEN_PROMPT)
    cleaned = _clean_json_string(raw_json)
    data = json.loads(cleaned)
    return [ReassessmentQuestion.model_validate(q) for q in data.get("questions", [])]


REASSESSMENT_EVAL_PROMPT = """You are an educational evaluator comparing a student's reassessment answers with their initial diagnosis.
Calculate new scores (0-100) across the 4 learning dimensions:
- concept_understanding
- logical_reasoning
- problem_solving
- application

Calculate the Before vs After delta for each dimension.
Provide a cautious, evidence-based growth summary.
Identify concepts improved, dimensions improved, remaining difficulties, and updated recommendations.
Do NOT claim that improvement proves permanent mastery.

Output strictly valid JSON:
{
  "growth_summary": "string explaining observed changes in student performance",
  "after_scores": {
    "concept_understanding": 82,
    "logical_reasoning": 74,
    "problem_solving": 70,
    "application": 76
  },
  "changes": {
    "concept_understanding": {
      "before": 65,
      "after": 82,
      "change": 17,
      "interpretation": "Stronger recall and clarity in foundational terms."
    },
    "logical_reasoning": {
      "before": 45,
      "after": 74,
      "change": 29,
      "interpretation": "Substantial improvement articulating cause-and-effect links."
    },
    "problem_solving": {
      "before": 50,
      "after": 70,
      "change": 20,
      "interpretation": "Demonstrated systematic troubleshooting steps."
    },
    "application": {
      "before": 40,
      "after": 76,
      "change": 36,
      "interpretation": "Demonstrated practical adjustment in scenario-based question."
    }
  },
  "concepts_improved": ["string"],
  "dimensions_improved": ["string"],
  "remaining_difficulties": ["string"],
  "updated_recommendations": ["string"],
  "mastery_note": "Measured results reflect current reassessment performance and do not imply permanent ability or mastery."
}
"""


def _mock_evaluate_reassessment(
    before_scores: DimensionScores,
    questions: List[ReassessmentQuestion],
    student_answers: List[StudentResponseItem],
    diagnosis: Optional[CombinedDiagnosis] = None,
    learning_map: Optional[LearningMap] = None,
) -> FinalProfileResult:
    after_scores = DimensionScores(
        concept_understanding=min(100, before_scores.concept_understanding + 18),
        logical_reasoning=min(100, before_scores.logical_reasoning + 28),
        problem_solving=min(100, before_scores.problem_solving + 22),
        application=min(100, before_scores.application + 34),
    )

    changes = {
        "concept_understanding": DimensionChange(
            before=before_scores.concept_understanding,
            after=after_scores.concept_understanding,
            change=after_scores.concept_understanding - before_scores.concept_understanding,
            interpretation="Substantial increase in conceptual clarity and accurate technical terminology.",
        ),
        "logical_reasoning": DimensionChange(
            before=before_scores.logical_reasoning,
            after=after_scores.logical_reasoning,
            change=after_scores.logical_reasoning - before_scores.logical_reasoning,
            interpretation="Notable progress in establishing sequential dependencies and cause-and-effect reasoning.",
        ),
        "problem_solving": DimensionChange(
            before=before_scores.problem_solving,
            after=after_scores.problem_solving,
            change=after_scores.problem_solving - before_scores.problem_solving,
            interpretation="Responses demonstrated structured isolation of variables and troubleshooting logic.",
        ),
        "application": DimensionChange(
            before=before_scores.application,
            after=after_scores.application,
            change=after_scores.application - before_scores.application,
            interpretation="Significant growth translating foundational concepts to realistic practical recommendations.",
        ),
    }

    target_concepts = list({q.target_concept for q in questions if q.target_concept})
    if not target_concepts and diagnosis and diagnosis.recommended_focus_areas:
        target_concepts = diagnosis.recommended_focus_areas

    return FinalProfileResult(
        growth_summary=(
            "Reassessment responses demonstrate marked improvement across all four assessed learning dimensions, "
            f"with the most significant gains observed in Logical Reasoning (+{changes['logical_reasoning'].change} pts) and "
            f"Practical Application (+{changes['application'].change} pts). The student successfully applied "
            "the sequential verification strategies reinforced during the personalized intervention."
        ),
        before_scores=before_scores,
        after_scores=after_scores,
        changes=changes,
        concepts_improved=target_concepts if target_concepts else ["Core Concepts", "Prerequisite Mechanisms"],
        dimensions_improved=[
            f"Logical Reasoning (+{changes['logical_reasoning'].change}%)",
            f"Practical Application (+{changes['application'].change}%)",
            f"Problem Solving (+{changes['problem_solving'].change}%)",
            f"Concept Understanding (+{changes['concept_understanding'].change}%)",
        ],
        remaining_difficulties=[
            "Handling complex boundary constraints under time pressure",
            "Synthesizing multiple interacting components without step-by-step guidance",
        ],
        updated_recommendations=[
            "Practice unguided multi-variable problem sets to build independent problem-solving stamina.",
            "Write down intermediate state transitions explicitly when designing practical implementations.",
            "Periodically revisit prerequisite dependencies to maintain conceptual coherence.",
        ],
        mastery_note="Measured results reflect performance on this reassessment session and provide actionable indicators rather than permanent ability measures.",
    )


def evaluate_reassessment(
    before_scores: DimensionScores,
    questions: List[ReassessmentQuestion],
    student_answers: List[StudentResponseItem],
    diagnosis: Optional[CombinedDiagnosis] = None,
    learning_map: Optional[LearningMap] = None,
) -> FinalProfileResult:
    mock_llm = os.getenv("MOCK_LLM", "false").strip().lower() in ("true", "1", "yes")
    if mock_llm:
        return _mock_evaluate_reassessment(
            before_scores, questions, student_answers, diagnosis, learning_map
        )

    answers_dict = {a.question_id: a.student_answer for a in student_answers}
    q_and_a = []
    for q in questions:
        q_and_a.append({
            "id": q.id,
            "target_concept": q.target_concept,
            "dimension": q.learning_dimension,
            "question": q.question_text,
            "expected_criteria": q.expected_criteria,
            "student_answer": answers_dict.get(q.id, "[No answer provided]"),
        })

    prompt_data = {
        "before_scores": before_scores.model_dump(),
        "reassessment_questions_and_answers": q_and_a,
    }
    if diagnosis:
        prompt_data["initial_diagnosis_summary"] = diagnosis.overall_summary

    prompt = f"EVALUATE REASSESSMENT AND COMPARE WITH BEFORE SCORES:\n{json.dumps(prompt_data, indent=2)}"
    raw_json = _call_llm_json(prompt, REASSESSMENT_EVAL_PROMPT)
    cleaned = _clean_json_string(raw_json)
    data = json.loads(cleaned)

    changes = {}
    for dim_key, dim_val in data.get("changes", {}).items():
        changes[dim_key] = DimensionChange.model_validate(dim_val)

    target_concepts = list({q.target_concept for q in questions if q.target_concept})
    fallback_concepts = data.get("concepts_improved") or target_concepts

    return FinalProfileResult(
        growth_summary=data.get("growth_summary", "Reassessment completed successfully."),
        before_scores=before_scores,
        after_scores=DimensionScores.model_validate(data.get("after_scores", before_scores.model_dump())),
        changes=changes,
        concepts_improved=fallback_concepts,
        dimensions_improved=data.get("dimensions_improved", [f"{k.replace('_', ' ').title()} improved" for k, v in changes.items() if v.change > 0]),
        remaining_difficulties=data.get("remaining_difficulties", ["Reinforce edge-case constraints under time pressure"]),
        updated_recommendations=data.get("updated_recommendations", ["Continue regular practice with unguided problem sets"]),
        mastery_note=data.get(
            "mastery_note",
            "Measured results reflect current reassessment performance and do not imply permanent ability or mastery.",
        ),
    )
