import React from 'react'

/**
 * Component to display the structured Learning Map returned by the AI backend.
 * Renders subject, topics, concepts, difficulty, prerequisites, and references.
 */
export default function LearningMapView({
  learningMap,
  onProceedToAnswerSheet,
  onProceedToAssessment,
  onResetStudyMaterial,
}) {
  if (!learningMap) return null

  const { subject, topics = [] } = learningMap

  // Calculate total concept count
  const totalConcepts = topics.reduce(
    (acc, topic) => acc + (topic.concepts ? topic.concepts.length : 0),
    0
  )

  const getDifficultyClass = (difficulty) => {
    if (!difficulty) return 'diff-badge-neutral'
    const diff = difficulty.toLowerCase()
    if (diff.includes('begin') || diff.includes('basic') || diff.includes('easy')) {
      return 'diff-badge-easy'
    }
    if (diff.includes('intermed') || diff.includes('medium')) {
      return 'diff-badge-medium'
    }
    if (diff.includes('advanc') || diff.includes('hard') || diff.includes('complex')) {
      return 'diff-badge-hard'
    }
    return 'diff-badge-neutral'
  }

  return (
    <section className="learning-map-container" aria-label="Structured Learning Map">
      <div className="learning-map-header">
        <div className="header-info">
          <span className="learning-map-tag">Generated Learning Map</span>
          <h2 className="learning-map-subject">{subject || 'Study Material'}</h2>
          <p className="learning-map-summary">
            {topics.length} Topic{topics.length === 1 ? '' : 's'} • {totalConcepts} Key Concept{totalConcepts === 1 ? '' : 's'} Mapped
          </p>
        </div>
        <div className="header-actions">
          {onProceedToAssessment && (
            <button
              type="button"
              className="primary-action-btn"
              onClick={onProceedToAssessment}
              title="Generate and take your diagnostic assessment"
            >
              Take Diagnostic Assessment →
            </button>
          )}
          {onProceedToAnswerSheet && (
            <button
              type="button"
              className="secondary-btn"
              onClick={onProceedToAnswerSheet}
              title="Continue to upload your previous answer sheet"
            >
              Upload Answer Sheet (Optional)
            </button>
          )}
          {onResetStudyMaterial && (
            <button
              type="button"
              className="secondary-btn"
              onClick={onResetStudyMaterial}
              title="Upload different study material"
            >
              Change Material
            </button>
          )}
        </div>
      </div>

      <div className="topics-grid">
        {topics.map((topicItem, topicIdx) => (
          <div key={topicIdx} className="topic-card">
            <div className="topic-header">
              <span className="topic-index">Topic {topicIdx + 1}</span>
              <h3 className="topic-title">{topicItem.topic}</h3>
            </div>

            <div className="concepts-list">
              {topicItem.concepts && topicItem.concepts.length > 0 ? (
                topicItem.concepts.map((concept, conceptIdx) => (
                  <div key={conceptIdx} className="concept-item">
                    <div className="concept-main-row">
                      <h4 className="concept-name">{concept.name}</h4>
                      <div className="concept-meta-badges">
                        {concept.difficulty && (
                          <span
                            className={`diff-badge ${getDifficultyClass(concept.difficulty)}`}
                            title={`Difficulty: ${concept.difficulty}`}
                          >
                            {concept.difficulty}
                          </span>
                        )}
                        {concept.source_reference && (
                          <span className="source-badge" title="Source reference">
                            📄 {concept.source_reference}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Prerequisites */}
                    {concept.prerequisites && concept.prerequisites.length > 0 && (
                      <div className="concept-relation-row">
                        <span className="relation-label">Prerequisites:</span>
                        <div className="relation-chips">
                          {concept.prerequisites.map((prereq, pIdx) => (
                            <span key={pIdx} className="relation-chip prereq-chip">
                              {prereq}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Related Concepts */}
                    {concept.related_concepts && concept.related_concepts.length > 0 && (
                      <div className="concept-relation-row">
                        <span className="relation-label">Related:</span>
                        <div className="relation-chips">
                          {concept.related_concepts.map((rel, rIdx) => (
                            <span key={rIdx} className="relation-chip related-chip">
                              {rel}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <p className="empty-concepts-note">No sub-concepts found for this topic.</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
