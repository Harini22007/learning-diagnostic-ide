import React, { useState } from 'react'

/**
 * InterventionView - Displays ONE unified personalized intervention targeting
 * the student's weakest dimensions and diagnosed prerequisite gaps.
 */
export default function InterventionView({
  intervention,
  learningMap,
  onProceedToReassessment,
  onBackToDiagnosis,
  isGeneratingReassessment = false,
}) {
  const [completedPrompts, setCompletedPrompts] = useState({})

  if (!intervention) {
    return (
      <div className="upload-card">
        <p className="section-description">No intervention pathway available.</p>
      </div>
    )
  }

  const {
    title,
    overview,
    weakness_focus_summary,
    suggested_learning_sequence = [],
    targeted_modules = [],
    study_recommendations = [],
  } = intervention

  const togglePrompt = (id) => {
    setCompletedPrompts((prev) => ({
      ...prev,
      [id]: !prev[id],
    }))
  }

  return (
    <div className="intervention-container">
      {/* Header Banner */}
      <div className="upload-card intervention-header-card">
        <div className="section-header-row">
          <div>
            <span className="step-badge">Step 6: Targeted Intervention</span>
            <h2 className="section-title">{title || 'Personalized Mastery Pathway'}</h2>
          </div>
          <span className="subject-pill">{learningMap?.subject || 'Targeted Learning'}</span>
        </div>

        <p className="intervention-overview-text">{overview}</p>

        {weakness_focus_summary && (
          <div className="weakness-focus-callout">
            <span className="focus-star-icon">⚡</span>
            <div>
              <strong>Weakness-Targeted Plan: </strong>
              <span>{weakness_focus_summary}</span>
            </div>
          </div>
        )}
      </div>

      {/* Suggested Learning Sequence */}
      {suggested_learning_sequence.length > 0 && (
        <div className="upload-card sequence-card">
          <h3 className="card-subheading">
            <span className="sequence-icon">🗺️</span> Recommended Learning Sequence
          </h3>
          <p className="section-description" style={{ marginBottom: '1rem' }}>
            Follow this sequenced roadmap to systematically resolve prerequisite gaps before re-testing:
          </p>

          <div className="sequence-steps-list">
            {suggested_learning_sequence.map((step, sIdx) => (
              <div key={sIdx} className="sequence-step-item">
                <div className="sequence-step-num">{sIdx + 1}</div>
                <div className="sequence-step-content">{step}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Targeted Modules */}
      <div className="modules-container">
        {targeted_modules.map((mod, mIdx) => (
          <div key={mIdx} className="upload-card module-card">
            <div className="module-header-row">
              <span className="module-badge">Targeted Concept Module</span>
              <h3 className="module-concept-title">{mod.concept}</h3>
            </div>

            {/* Identified Gap Alert */}
            <div className="module-gap-banner">
              <span className="gap-alert-icon">🔍</span>
              <div>
                <strong>Diagnosed Learning Gap:</strong> {mod.identified_gap}
              </div>
            </div>

            {/* Prerequisite Refresher */}
            {mod.prerequisite_refresher && (
              <div className="refresher-box">
                <div className="refresher-title">
                  <span>🔄</span> Prerequisite Foundations Refresher
                </div>
                <p className="refresher-content">{mod.prerequisite_refresher}</p>
              </div>
            )}

            {/* Core Explanation */}
            <div className="core-explanation-section">
              <h4 className="section-mini-heading">Intuitive Conceptual Mechanics</h4>
              <p className="core-explanation-text">{mod.core_explanation}</p>
            </div>

            {/* Misconception Clarification */}
            {mod.misconception_clarification && (
              <div className="misconception-callout-box">
                <div className="misconception-callout-title">
                  <span>💡</span> Common Pitfall & Clarification
                </div>
                <p className="misconception-callout-text">{mod.misconception_clarification}</p>
              </div>
            )}

            {/* Worked Example */}
            {mod.worked_example && (
              <div className="worked-example-box">
                <h4 className="worked-example-heading">
                  <span>📐</span> Step-by-Step Guided Walkthrough
                </h4>
                <pre className="worked-example-pre">{mod.worked_example}</pre>
              </div>
            )}

            {/* Practice Self-Check Prompts */}
            {mod.practice_prompts && mod.practice_prompts.length > 0 && (
              <div className="practice-prompts-section">
                <h4 className="section-mini-heading">
                  <span>✍️</span> Active Self-Check Practice Prompts
                </h4>
                <p className="practice-subtitle">
                  Test your understanding before starting the reassessment:
                </p>

                <div className="prompts-list">
                  {mod.practice_prompts.map((prompt, pIdx) => {
                    const promptKey = `${mIdx}_${pIdx}`
                    const isDone = !!completedPrompts[promptKey]
                    return (
                      <div
                        key={pIdx}
                        className={`prompt-item ${isDone ? 'completed' : ''}`}
                        onClick={() => togglePrompt(promptKey)}
                      >
                        <input
                          type="checkbox"
                          className="prompt-checkbox"
                          checked={isDone}
                          onChange={() => togglePrompt(promptKey)}
                          onClick={(e) => e.stopPropagation()}
                        />
                        <span className="prompt-text">{prompt}</span>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* General Study Recommendations */}
      {study_recommendations.length > 0 && (
        <div className="upload-card study-recs-card">
          <h3 className="card-subheading">
            <span className="study-icon">📚</span> Actionable Study Strategies
          </h3>
          <ul className="study-recs-list">
            {study_recommendations.map((rec, rIdx) => (
              <li key={rIdx} className="study-rec-item">
                {rec}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Action Row */}
      <div className="action-row-split" style={{ marginTop: '2rem' }}>
        <button
          type="button"
          className="secondary-btn"
          onClick={onBackToDiagnosis}
          disabled={isGeneratingReassessment}
        >
          ← Back to Diagnosis
        </button>

        <button
          type="button"
          className="primary-btn pulse-glow-btn"
          onClick={onProceedToReassessment}
          disabled={isGeneratingReassessment}
        >
          {isGeneratingReassessment ? (
            <>
              <span className="inline-spinner" /> Generating Targeted Reassessment...
            </>
          ) : (
            'Take Targeted Reassessment →'
          )}
        </button>
      </div>
    </div>
  )
}
