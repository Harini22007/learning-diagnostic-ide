import React, { useState } from 'react'

/**
 * DiagnosisView - Synthesized evidence-based learning diagnosis across 4 dimensions with
 * concept-level performance, root causes with confidence levels, and per-question criteria rubrics.
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
    dimension_scores,
    dimension_averages,
    concept_scores = [],
    topic_diagnosis = [],
    possible_root_causes = [],
    prerequisite_gaps = [],
    recommended_focus = [],
    recommended_focus_areas = [],
    evaluated_questions = [],
    previous_evidence_summary,
    current_evidence_summary,
    combined_conclusion,
    confidence = 'Medium',
  } = diagnosis

  const activeDimScores = dimension_scores || dimension_averages
  const activeFocusAreas = (recommended_focus && recommended_focus.length > 0)
    ? recommended_focus
    : (recommended_focus_areas || [])

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
      score: activeDimScores?.concept_understanding ?? 0,
      desc: 'Definitions, core properties, and accurate conceptual recall',
      color: 'var(--accent-blue, #3b82f6)',
    },
    {
      key: 'logical_reasoning',
      label: 'Logical Reasoning',
      score: activeDimScores?.logical_reasoning ?? 0,
      desc: 'Cause-and-effect chains, deductive deduction, and prerequisite flow',
      color: 'var(--accent-purple, #8b5cf6)',
    },
    {
      key: 'problem_solving',
      label: 'Problem Solving',
      score: activeDimScores?.problem_solving ?? 0,
      desc: 'Scenario troubleshooting, error isolation, and edge-case handling',
      color: 'var(--accent-emerald, #10b981)',
    },
    {
      key: 'application',
      label: 'Practical / Application',
      score: activeDimScores?.application ?? 0,
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

  const getConfidenceBadgeClass = (conf) => {
    const c = (conf || 'Medium').toLowerCase()
    if (c === 'high') return 'badge-conf-high'
    if (c === 'medium') return 'badge-conf-medium'
    return 'badge-conf-low'
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
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <span className="subject-pill">{learningMap?.subject || 'Curriculum Analysis'}</span>
            <span className={`confidence-pill ${getConfidenceBadgeClass(confidence)}`}>
              Confidence: {confidence}
            </span>
          </div>
        </div>

        <p className="diagnosis-summary-text">{overall_summary}</p>

        <div className="cautious-disclaimer-box">
          <span className="disclaimer-icon">ℹ️</span>
          <span>
            <strong>Assessment Methodology:</strong> Evaluations reflect observed student responses across
            the four learning dimensions and previous answer sheet evidence. They identify actionable friction
            areas rather than permanent ability or intelligence.
          </span>
        </div>
      </div>

      {/* Previous Answer Sheet vs Current Diagnostic Evidence (if available) */}
      {(previous_evidence_summary || combined_conclusion) && (
        <div className="upload-card evidence-comparison-card">
          <h3 className="card-subheading">Assessment Evidence Integration</h3>
          <p className="section-description" style={{ margin: '0 0 1rem 0' }}>
            Comparison between historical answer sheet signals and current diagnostic test responses:
          </p>

          <div className="evidence-comparison-grid">
            {previous_evidence_summary && (
              <div className="evidence-source-block prev-block">
                <span className="evidence-block-label">Previous Answer Sheet Evidence</span>
                <p className="evidence-block-text">{previous_evidence_summary}</p>
              </div>
            )}
            {current_evidence_summary && (
              <div className="evidence-source-block curr-block">
                <span className="evidence-block-label">Current Diagnostic Test Evidence</span>
                <p className="evidence-block-text">{current_evidence_summary}</p>
              </div>
            )}
            {combined_conclusion && (
              <div className="evidence-source-block combined-block">
                <span className="evidence-block-label">Combined Evidence Conclusion</span>
                <p className="evidence-block-text">{combined_conclusion}</p>
              </div>
            )}
          </div>
        </div>
      )}

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

      {/* Concept & Topic Performance from Actual Question Evidence */}
      {concept_scores.length > 0 && (
        <div className="upload-card concept-performance-card">
          <div className="section-header-row">
            <div>
              <h3 className="card-subheading">Concept & Topic Performance Breakdown</h3>
              <p className="section-description" style={{ margin: 0 }}>
                Evaluated performance calculated strictly from question evidence:
              </p>
            </div>
          </div>

          <div className="concept-performance-grid">
            {concept_scores.map((cs, idx) => (
              <div key={idx} className="concept-perf-item">
                <div className="concept-perf-header">
                  <div>
                    <span className="concept-perf-name">{cs.concept}</span>
                    <span className="concept-perf-topic">under {cs.topic}</span>
                  </div>
                  <span className={`dimension-badge ${getScoreBadgeClass(cs.percentage)}`}>
                    {cs.performance_level || getScoreStatusLabel(cs.percentage)}
                  </span>
                </div>

                <div className="concept-perf-bar-row">
                  <div className="dimension-bar-track" style={{ height: '6px' }}>
                    <div
                      className="dimension-bar-fill"
                      style={{
                        width: `${cs.percentage}%`,
                        backgroundColor: cs.percentage >= 75 ? '#16a34a' : cs.percentage >= 50 ? '#d97706' : '#dc2626',
                      }}
                    />
                  </div>
                  <span className="concept-perf-score-text">
                    {cs.marks_awarded} / {cs.marks_possible} Marks ({cs.percentage}%)
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Root Causes & Topic Diagnosis */}
      {(possible_root_causes.length > 0 || topic_diagnosis.length > 0) && (
        <div className="upload-card diagnosis-details-card">
          <h3 className="card-subheading">Identified Learning Friction & Possible Root Causes</h3>

          <div className="topic-diagnosis-list">
            {(possible_root_causes.length > 0 ? possible_root_causes : topic_diagnosis).map((item, idx) => {
              const isRootCauseObj = !!item.root_cause
              const conceptName = isRootCauseObj ? item.affected_concept : item.concept
              const topicName = !isRootCauseObj ? item.topic : null
              const rootCauseText = isRootCauseObj ? item.root_cause : item.possible_root_cause
              const frictionText = !isRootCauseObj ? item.primary_difficulty : null
              const evidenceList = isRootCauseObj ? item.supporting_evidence : item.evidence
              const confLevel = isRootCauseObj ? item.confidence_level : (item.confidence || 'Medium')

              return (
                <div key={idx} className="topic-diag-item">
                  <div className="topic-diag-header">
                    <span className="concept-pill">{conceptName}</span>
                    {topicName && <span className="topic-subtle-tag">under {topicName}</span>}
                    <span className={`confidence-pill ${getConfidenceBadgeClass(confLevel)}`} style={{ marginLeft: 'auto' }}>
                      Confidence: {confLevel}
                    </span>
                  </div>

                  <div className="friction-grid">
                    {frictionText && (
                      <div className="friction-block">
                        <span className="friction-label">Observed Friction Point</span>
                        <p className="friction-text">{frictionText}</p>
                      </div>
                    )}
                    <div className="friction-block root-cause-block" style={{ gridColumn: frictionText ? undefined : '1 / -1' }}>
                      <span className="friction-label">Possible Root Cause</span>
                      <p className="friction-text">{rootCauseText}</p>
                    </div>
                  </div>

                  {evidenceList && evidenceList.length > 0 && (
                    <div className="evidence-list-box">
                      <span className="evidence-label">Supporting Evidence from Answers:</span>
                      <ul className="evidence-bullet-list">
                        {evidenceList.map((ev, evIdx) => (
                          <li key={evIdx}>{ev}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )
            })}
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
            Reinforcing foundational dependencies to unlock deeper multi-step reasoning:
          </p>
          <div className="tags-container">
            {prerequisite_gaps.length > 0 ? (
              prerequisite_gaps.map((gap, gIdx) => (
                <span key={gIdx} className="prereq-gap-tag">
                  {gap}
                </span>
              ))
            ) : (
              <span className="empty-tag">No clear prerequisite gap established from the available evidence.</span>
            )}
          </div>
        </div>

        <div className="upload-card focus-card">
          <h3 className="card-subheading">
            <span className="focus-icon">🎯</span> Recommended Focus Areas
          </h3>
          <p className="focus-description">
            High-leverage concepts where targeted reinforcement will produce the greatest mastery gains:
          </p>
          <div className="tags-container">
            {activeFocusAreas.length > 0 ? (
              activeFocusAreas.map((focus, fIdx) => (
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
                Expand each question to inspect the criteria-based rubric evaluation, awarded marks, and detected misconceptions.
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
              const marksAwarded = eq.marks_awarded !== undefined ? eq.marks_awarded : eq.score
              const pct = eq.percentage !== undefined ? eq.percentage : Math.round((marksAwarded / eq.marks_possible) * 100)

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
                      <span className="eval-dim-pill">{eq.learning_dimension || eq.dimension}</span>
                      <span className="eval-concept-name">{eq.concept}</span>
                    </div>
                    <div className="eval-q-right">
                      <span className="eval-score-chip">
                        {marksAwarded} / {eq.marks_possible} Marks ({pct}%)
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

                      {eq.missing_elements && eq.missing_elements.length > 0 && (
                        <div className="eval-detail-row">
                          <span className="eval-detail-label">Missing Elements:</span>
                          <ul className="evidence-bullet-list" style={{ marginTop: '0.25rem' }}>
                            {eq.missing_elements.map((me, meIdx) => (
                              <li key={meIdx}>{me}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {(eq.misconceptions_detected || (eq.misconceptions && eq.misconceptions.length > 0)) && (
                        <div className="eval-detail-row misconception-alert-row">
                          <span className="eval-detail-label">Misconception Identified:</span>
                          <p className="eval-misconception-text">
                            ⚠️ {eq.misconceptions_detected || eq.misconceptions.join('; ')}
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
