import React, { useState } from 'react'

/**
 * DiagnosisView - Synthesized learning diagnosis across 4 dimensions with
 * per-question evaluation criteria, detected misconceptions, and root cause analysis.
 */
export default function DiagnosisView({
  diagnosis,
  learningMap,
  onProceedToIntervention,
  onBackToMap,
  isGeneratingIntervention = false,
}) {
  const [expandedQuestions, setExpandedQuestions] = useState({})

  if (!diagnosis) {
    return (
      <div className="upload-card">
        <p className="section-description">No diagnosis data available.</p>
      </div>
    )
  }

  const {
    overall_summary,
    dimension_averages,
    topic_diagnosis = [],
    prerequisite_gaps = [],
    recommended_focus_areas = [],
    evaluated_questions = [],
  } = diagnosis

  const toggleQuestion = (qId) => {
    setExpandedQuestions((prev) => ({
      ...prev,
      [qId]: !prev[qId],
    }))
  }

  // Dimension details helper
  const dimensionsMeta = [
    {
      key: 'concept_understanding',
      label: 'Concept Understanding',
      score: dimension_averages?.concept_understanding ?? 0,
      desc: 'Definitions, core properties, and accurate conceptual recall',
      color: 'var(--accent-blue, #3b82f6)',
    },
    {
      key: 'logical_reasoning',
      label: 'Logical Reasoning',
      score: dimension_averages?.logical_reasoning ?? 0,
      desc: 'Cause-and-effect chains, deductive deduction, and prerequisite flow',
      color: 'var(--accent-purple, #8b5cf6)',
    },
    {
      key: 'problem_solving',
      label: 'Problem Solving',
      score: dimension_averages?.problem_solving ?? 0,
      desc: 'Scenario troubleshooting, error isolation, and edge-case handling',
      color: 'var(--accent-emerald, #10b981)',
    },
    {
      key: 'application',
      label: 'Practical / Application',
      score: dimension_averages?.application ?? 0,
      desc: 'Applying concepts to real-world workflows and operational implementations',
      color: 'var(--accent-amber, #f59e0b)',
    },
  ]

  const getScoreBadgeClass = (score) => {
    if (score >= 75) return 'badge-proficient'
    if (score >= 50) return 'badge-developing'
    return 'badge-needs-focus'
  }

  const getScoreStatusLabel = (score) => {
    if (score >= 75) return 'Solid'
    if (score >= 50) return 'Developing'
    return 'Needs Focus'
  }

  return (
    <div className="diagnosis-container">
      {/* Header Banner */}
      <div className="upload-card diagnosis-header-card">
        <div className="section-header-row">
          <div>
            <span className="step-badge">Step 5: Diagnostic Synthesis</span>
            <h2 className="section-title">Evidence-Based Learning Diagnosis</h2>
          </div>
          <span className="subject-pill">{learningMap?.subject || 'Curriculum Analysis'}</span>
        </div>

        <p className="diagnosis-summary-text">{overall_summary}</p>

        <div className="cautious-disclaimer-box">
          <span className="disclaimer-icon">ℹ️</span>
          <span>
            <strong>Assessment Methodology:</strong> Evaluations reflect observed answers on this diagnostic test
            and previous answer sheet evidence. They highlight specific friction areas rather than permanent ability.
          </span>
        </div>
      </div>

      {/* 4 Learning Dimensions Gauges */}
      <div className="dimensions-grid">
        {dimensionsMeta.map((dim) => (
          <div key={dim.key} className="dimension-card">
            <div className="dimension-card-header">
              <span className="dimension-label">{dim.label}</span>
              <span className={`dimension-badge ${getScoreBadgeClass(dim.score)}`}>
                {getScoreStatusLabel(dim.score)}
              </span>
            </div>

            <div className="dimension-score-row">
              <span className="dimension-number">{dim.score}%</span>
              <span className="dimension-scale">/ 100</span>
            </div>

            <div className="dimension-bar-track">
              <div
                className="dimension-bar-fill"
                style={{
                  width: `${dim.score}%`,
                  backgroundColor: dim.color,
                }}
              />
            </div>

            <p className="dimension-desc">{dim.desc}</p>
          </div>
        ))}
      </div>

      {/* Root Causes & Topic Diagnosis */}
      {topic_diagnosis.length > 0 && (
        <div className="upload-card diagnosis-details-card">
          <h3 className="card-subheading">Identified Learning Friction & Possible Root Causes</h3>

          <div className="topic-diagnosis-list">
            {topic_diagnosis.map((td, idx) => (
              <div key={idx} className="topic-diag-item">
                <div className="topic-diag-header">
                  <span className="concept-pill">{td.concept}</span>
                  <span className="topic-subtle-tag">under {td.topic}</span>
                </div>

                <div className="friction-grid">
                  <div className="friction-block">
                    <span className="friction-label">Observed Friction Point</span>
                    <p className="friction-text">{td.primary_difficulty}</p>
                  </div>
                  <div className="friction-block root-cause-block">
                    <span className="friction-label">Possible Root Cause</span>
                    <p className="friction-text">{td.possible_root_cause}</p>
                  </div>
                </div>

                {td.evidence && td.evidence.length > 0 && (
                  <div className="evidence-list-box">
                    <span className="evidence-label">Observations from Answers:</span>
                    <ul className="evidence-bullet-list">
                      {td.evidence.map((ev, evIdx) => (
                        <li key={evIdx}>{ev}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Prerequisite Gaps & Focus Recommendations */}
      <div className="gaps-and-focus-grid">
        <div className="upload-card gaps-card">
          <h3 className="card-subheading">
            <span className="gap-icon">⚠️</span> Diagnosed Prerequisite Gaps
          </h3>
          <p className="gaps-description">
            Reinforcing these foundational ideas will unlock stronger logical reasoning downstream:
          </p>
          <div className="tags-container">
            {prerequisite_gaps.length > 0 ? (
              prerequisite_gaps.map((gap, gIdx) => (
                <span key={gIdx} className="prereq-gap-tag">
                  {gap}
                </span>
              ))
            ) : (
              <span className="empty-tag">No major prerequisite gaps detected</span>
            )}
          </div>
        </div>

        <div className="upload-card focus-card">
          <h3 className="card-subheading">
            <span className="focus-icon">🎯</span> Recommended Focus Areas
          </h3>
          <p className="focus-description">
            High-leverage topics where targeted review will produce the greatest mastery gains:
          </p>
          <div className="tags-container">
            {recommended_focus_areas.length > 0 ? (
              recommended_focus_areas.map((focus, fIdx) => (
                <span key={fIdx} className="focus-area-tag">
                  {focus}
                </span>
              ))
            ) : (
              <span className="empty-tag">Core topics in curriculum</span>
            )}
          </div>
        </div>
      </div>

      {/* Evaluated Questions Breakdown */}
      {evaluated_questions.length > 0 && (
        <div className="upload-card evaluated-questions-card">
          <div className="section-header-row">
            <div>
              <h3 className="card-subheading">Question-Specific Evaluation Details</h3>
              <p className="section-description" style={{ margin: 0 }}>
                Expand each question to inspect the criteria-based rubric evaluation and detected misconceptions.
              </p>
            </div>
            <button
              type="button"
              className="view-link-btn"
              onClick={() => {
                const allExpanded = Object.keys(expandedQuestions).length === evaluated_questions.length
                if (allExpanded) {
                  setExpandedQuestions({})
                } else {
                  const expandAll = {}
                  evaluated_questions.forEach((q) => {
                    expandAll[q.question_id] = true
                  })
                  setExpandedQuestions(expandAll)
                }
              }}
            >
              {Object.keys(expandedQuestions).length === evaluated_questions.length
                ? 'Collapse All'
                : 'Expand All'}
            </button>
          </div>

          <div className="evaluated-questions-list">
            {evaluated_questions.map((eq, qIdx) => {
              const isExpanded = !!expandedQuestions[eq.question_id]
              return (
                <div key={eq.question_id} className={`eval-q-item ${isExpanded ? 'expanded' : ''}`}>
                  <button
                    type="button"
                    className="eval-q-summary-row"
                    onClick={() => toggleQuestion(eq.question_id)}
                    aria-expanded={isExpanded}
                  >
                    <div className="eval-q-left">
                      <span className="eval-q-num">Q{qIdx + 1}</span>
                      <span className="eval-dim-pill">{eq.dimension}</span>
                      <span className="eval-concept-name">{eq.concept}</span>
                    </div>
                    <div className="eval-q-right">
                      <span className="eval-score-chip">
                        {eq.score} / {eq.marks_possible} Marks
                      </span>
                      <span className="eval-expand-arrow">{isExpanded ? '▲' : '▼'}</span>
                    </div>
                  </button>

                  {isExpanded && (
                    <div className="eval-q-details-body">
                      <div className="eval-detail-row">
                        <span className="eval-detail-label">Question Prompt:</span>
                        <p className="eval-detail-prompt">{eq.question_text}</p>
                      </div>

                      <div className="eval-detail-row">
                        <span className="eval-detail-label">Your Submitted Answer:</span>
                        <div className="eval-student-answer-box">
                          {eq.student_answer || '[No response submitted]'}
                        </div>
                      </div>

                      <div className="eval-detail-row">
                        <span className="eval-detail-label">Rubric Evaluation:</span>
                        <p className="eval-rubric-text">{eq.rubric_evaluation}</p>
                      </div>

                      {eq.misconceptions_detected && (
                        <div className="eval-detail-row misconception-alert-row">
                          <span className="eval-detail-label">Misconception Identified:</span>
                          <p className="eval-misconception-text">
                            ⚠️ {eq.misconceptions_detected}
                          </p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Action Row */}
      <div className="action-row-split" style={{ marginTop: '2rem' }}>
        <button
          type="button"
          className="secondary-btn"
          onClick={onBackToMap}
          disabled={isGeneratingIntervention}
        >
          ← Back to Learning Map
        </button>

        <button
          type="button"
          className="primary-btn pulse-glow-btn"
          onClick={onProceedToIntervention}
          disabled={isGeneratingIntervention}
        >
          {isGeneratingIntervention ? (
            <>
              <span className="inline-spinner" /> Generating Personalized Intervention...
            </>
          ) : (
            'Generate ONE Personalized Intervention →'
          )}
        </button>
      </div>
    </div>
  )
}
