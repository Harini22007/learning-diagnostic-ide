import React, { useState } from 'react'

/**
 * ReassessmentView - Clean, student-friendly reassessment test taking interface.
 * IMPORTANT: Internal learning-dimension labels and evaluation criteria are strictly
 * hidden from the student during test taking.
 */
export default function ReassessmentView({
  questions = [],
  onSubmitAnswers,
  onBackToIntervention,
  isEvaluating = false,
}) {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [answers, setAnswers] = useState({})
  const [isReviewMode, setIsReviewMode] = useState(false)

  const currentQ = questions[currentIndex]
  const totalQuestions = questions.length

  const handleAnswerChange = (qId, text) => {
    setAnswers((prev) => ({ ...prev, [qId]: text }))
  }

  const answeredCount = Object.keys(answers).filter(
    (k) => answers[k] && answers[k].trim().length > 0
  ).length

  const handleFinalSubmit = () => {
    const formatted = questions.map((q) => ({
      question_id: q.id,
      student_answer: (answers[q.id] || '').trim(),
    }))
    onSubmitAnswers(formatted)
  }

  if (isReviewMode) {
    return (
      <div className="upload-card assessment-review-card">
        <div className="section-header-row">
          <div>
            <span className="step-badge">Reassessment Review</span>
            <h2 className="section-title">Review Your Reassessment Answers</h2>
          </div>
          <button
            type="button"
            className="view-link-btn"
            onClick={() => setIsReviewMode(false)}
          >
            ← Back to Questions
          </button>
        </div>

        <p className="section-description">
          Review your responses before submitting for final Before vs After growth evaluation.
          You have answered <strong>{answeredCount} of {totalQuestions}</strong> questions.
        </p>

        <div className="review-list">
          {questions.map((q, idx) => (
            <div key={q.id} className="review-item">
              <div className="review-header">
                <span className="review-q-num">Reassessment Question {idx + 1}</span>
                <span className="review-topic-badge">{q.target_concept}</span>
                <button
                  type="button"
                  className="review-edit-btn"
                  onClick={() => {
                    setCurrentIndex(idx)
                    setIsReviewMode(false)
                  }}
                >
                  Edit
                </button>
              </div>
              <p className="review-q-text">{q.question_text || q.question}</p>
              <div className="review-answer-box">
                {answers[q.id] && answers[q.id].trim() ? (
                  <p className="review-student-answer">{answers[q.id]}</p>
                ) : (
                  <p className="review-unanswered">[No response entered]</p>
                )}
              </div>
            </div>
          ))}
        </div>

        <div className="action-row-split">
          <button
            type="button"
            className="secondary-btn"
            onClick={() => setIsReviewMode(false)}
            disabled={isEvaluating}
          >
            ← Back to Questions
          </button>

          <button
            type="button"
            className="primary-btn pulse-glow-btn"
            onClick={handleFinalSubmit}
            disabled={isEvaluating || answeredCount === 0}
          >
            {isEvaluating ? (
              <>
                <span className="inline-spinner" /> Evaluating Growth & Deltas...
              </>
            ) : (
              'Submit Reassessment for Growth Analysis →'
            )}
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="upload-card assessment-card">
      <div className="assessment-header">
        <div className="assessment-progress-info">
          <span className="step-badge">Targeted Reassessment</span>
          <span className="progress-counter">
            Question {currentIndex + 1} of {totalQuestions}
          </span>
        </div>
        <div className="progress-bar-track">
          <div
            className="progress-bar-fill"
            style={{ width: `${((currentIndex + 1) / totalQuestions) * 100}%` }}
          />
        </div>
      </div>

      {currentQ && (
        <div className="question-display-area">
          <div className="question-context-row">
            <span className="topic-context-tag">Target Concept: {currentQ.target_concept}</span>
          </div>

          <h3 className="diagnostic-question-text">{currentQ.question_text || currentQ.question}</h3>

          <div className="answer-input-container">
            <label htmlFor={`reassess-answer-${currentQ.id}`} className="answer-input-label">
              Your Reassessment Answer:
            </label>
            <textarea
              id={`reassess-answer-${currentQ.id}`}
              className="answer-textarea"
              rows={6}
              placeholder="Apply the concepts and verification strategies from your intervention..."
              value={answers[currentQ.id] || ''}
              onChange={(e) => handleAnswerChange(currentQ.id, e.target.value)}
              disabled={isEvaluating}
            />
          </div>
        </div>
      )}

      <div className="action-row-split">
        <button
          type="button"
          className="secondary-btn"
          onClick={() => {
            if (currentIndex > 0) setCurrentIndex(currentIndex - 1)
            else onBackToIntervention()
          }}
          disabled={isEvaluating}
        >
          {currentIndex === 0 ? '← Back to Intervention' : '← Previous Question'}
        </button>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          {currentIndex < totalQuestions - 1 ? (
            <button
              type="button"
              className="primary-btn"
              onClick={() => setCurrentIndex(currentIndex + 1)}
              disabled={isEvaluating}
            >
              Next Question →
            </button>
          ) : (
            <button
              type="button"
              className="primary-btn pulse-glow-btn"
              onClick={() => setIsReviewMode(true)}
              disabled={isEvaluating}
            >
              Review & Submit Reassessment →
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
