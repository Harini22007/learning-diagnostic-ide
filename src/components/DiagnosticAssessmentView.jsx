import React, { useState } from 'react'

/**
 * DiagnosticAssessmentView - Clean, student-friendly test taking interface.
 * IMPORTANT: Internal learning-dimension labels are strictly hidden from the student.
 */
export default function DiagnosticAssessmentView({
  questions = [],
  onSubmitAnswers,
  onBack,
  isDiagnosing = false,
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
            <span className="step-badge">Review Step</span>
            <h2 className="section-title">Review Your Diagnostic Answers</h2>
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
          Review your answers below before submitting for learning diagnosis. You have answered{' '}
          <strong>{answeredCount} of {totalQuestions}</strong> questions.
        </p>

        <div className="review-list">
          {questions.map((q, idx) => (
            <div key={q.id} className="review-item">
              <div className="review-header">
                <span className="review-q-num">Question {idx + 1}</span>
                <span className="review-topic-badge">{q.topic}</span>
                <span className="review-marks-badge">{q.marks || 5} Marks</span>
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
              <p className="review-q-text">{q.question || q.question_text}</p>
              <div className="review-answer-box">
                {answers[q.id] && answers[q.id].trim() ? (
                  <p className="review-student-answer">{answers[q.id]}</p>
                ) : (
                  <p className="review-unanswered">[No answer entered]</p>
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
            disabled={isDiagnosing}
          >
            ← Back to Questions
          </button>

          <button
            type="button"
            className="primary-btn"
            onClick={handleFinalSubmit}
            disabled={isDiagnosing || answeredCount === 0}
          >
            {isDiagnosing ? 'Submitting Answers...' : 'Submit Assessment →'}
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="upload-card assessment-card">
      <div className="assessment-header">
        <div className="assessment-progress-info">
          <span className="step-badge">Diagnostic Assessment</span>
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
            <span className="topic-context-tag">Topic: {currentQ.topic}</span>
            <span className="difficulty-context-tag">{currentQ.difficulty}</span>
            <span className="marks-context-tag">{currentQ.marks || 5} Marks</span>
          </div>

          <h3 className="diagnostic-question-text">{currentQ.question || currentQ.question_text}</h3>

          <div className="answer-input-container">
            <label htmlFor={`answer-${currentQ.id}`} className="answer-input-label">
              Your Answer:
            </label>
            <textarea
              id={`answer-${currentQ.id}`}
              className="answer-textarea"
              rows={6}
              placeholder="Type your explanation, reasoning, or solution here..."
              value={answers[currentQ.id] || ''}
              onChange={(e) => handleAnswerChange(currentQ.id, e.target.value)}
              disabled={isDiagnosing}
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
            else onBack()
          }}
          disabled={isDiagnosing}
        >
          {currentIndex === 0 ? '← Exit Assessment' : '← Previous Question'}
        </button>

        <div className="assessment-right-actions">
          <button
            type="button"
            className="review-nav-btn"
            onClick={() => setIsReviewMode(true)}
          >
            Review ({answeredCount}/{totalQuestions})
          </button>

          {currentIndex < totalQuestions - 1 ? (
            <button
              type="button"
              className="primary-btn"
              onClick={() => setCurrentIndex(currentIndex + 1)}
            >
              Next Question →
            </button>
          ) : (
            <button
              type="button"
              className="primary-btn"
              onClick={() => setIsReviewMode(true)}
            >
              Review & Submit →
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
