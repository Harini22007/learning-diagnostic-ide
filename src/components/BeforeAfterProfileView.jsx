import React from 'react'

/**
 * BeforeAfterProfileView - Comprehensive Before vs After Learning Profile
 * showing growth deltas across all 4 learning dimensions, concepts improved,
 * remaining difficulties, and updated actionable recommendations.
 */
export default function BeforeAfterProfileView({
  profile,
  learningMap,
  onRestart,
  onViewLearningMap,
}) {
  if (!profile) {
    return (
      <div className="upload-card">
        <p className="section-description">No reassessment profile data available.</p>
      </div>
    )
  }

  const {
    growth_summary,
    before_scores,
    after_scores,
    changes = {},
    concepts_improved = [],
    dimensions_improved = [],
    remaining_difficulties = [],
    updated_recommendations = [],
    mastery_note,
  } = profile

  const dimensionsList = [
    {
      key: 'concept_understanding',
      label: 'Concept Understanding',
      desc: 'Definitions, properties, and fundamental recall',
      color: 'var(--accent-blue, #3b82f6)',
    },
    {
      key: 'logical_reasoning',
      label: 'Logical Reasoning',
      desc: 'Cause-and-effect, deductive chains, and prerequisite flow',
      color: 'var(--accent-purple, #8b5cf6)',
    },
    {
      key: 'problem_solving',
      label: 'Problem Solving',
      desc: 'Systematic troubleshooting, variable isolation, and solutions',
      color: 'var(--accent-emerald, #10b981)',
    },
    {
      key: 'application',
      label: 'Practical / Application',
      desc: 'Real-world transfer, implementation trade-offs, and systems',
      color: 'var(--accent-amber, #f59e0b)',
    },
  ]

  return (
    <div className="profile-container">
      {/* Celebration & Growth Narrative Header */}
      <div className="upload-card profile-header-card">
        <div className="profile-celebration-badge">🚀 Measurable Growth Detected</div>
        <h2 className="section-title" style={{ fontSize: '2rem', marginTop: '0.5rem' }}>
          Before vs After Learning Profile
        </h2>
        <span className="subject-pill">{learningMap?.subject || 'Curriculum Reassessment'}</span>

        <p className="growth-summary-narrative">{growth_summary}</p>

        {mastery_note && (
          <div className="cautious-disclaimer-box" style={{ marginTop: '1.25rem' }}>
            <span className="disclaimer-icon">ℹ️</span>
            <span>{mastery_note}</span>
          </div>
        )}
      </div>

      {/* Side-by-Side Dimension Comparison */}
      <div className="upload-card dimension-comparison-card">
        <div className="section-header-row">
          <div>
            <h3 className="card-subheading">Learning Dimension Delta Comparison</h3>
            <p className="section-description" style={{ margin: 0 }}>
              Performance across 4 core dimensions before vs after targeted intervention:
            </p>
          </div>
          <div className="comparison-legend">
            <span className="legend-item">
              <span className="legend-swatch before-swatch" /> Before Intervention
            </span>
            <span className="legend-item">
              <span className="legend-swatch after-swatch" /> After Reassessment
            </span>
          </div>
        </div>

        <div className="dimensions-comparison-list">
          {dimensionsList.map((dim) => {
            const beforeVal = before_scores?.[dim.key] ?? 0
            const afterVal = after_scores?.[dim.key] ?? 0
            const changeData = changes[dim.key] || {}
            const delta = changeData.change ?? afterVal - beforeVal

            return (
              <div key={dim.key} className="comparison-row-item">
                <div className="comparison-row-header">
                  <div>
                    <span className="comparison-dim-title">{dim.label}</span>
                    <span className="comparison-dim-desc">{dim.desc}</span>
                  </div>
                  <div className="comparison-badges-group">
                    <span className="before-score-tag">Before: {beforeVal}%</span>
                    <span className="after-score-tag">After: {afterVal}%</span>
                    <span className={`delta-badge ${delta > 0 ? 'positive-delta' : 'neutral-delta'}`}>
                      {delta >= 0 ? `+${delta}%` : `${delta}%`}
                    </span>
                  </div>
                </div>

                {/* Dual Progress Bar */}
                <div className="dual-progress-container">
                  <div className="dual-bar before-bar">
                    <div className="bar-fill before-fill" style={{ width: `${beforeVal}%` }} />
                  </div>
                  <div className="dual-bar after-bar">
                    <div
                      className="bar-fill after-fill"
                      style={{ width: `${afterVal}%`, backgroundColor: dim.color }}
                    />
                  </div>
                </div>

                {changeData.interpretation && (
                  <p className="comparison-interpretation-text">
                    <strong>Evidence: </strong> {changeData.interpretation}
                  </p>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Improved Concepts & Dimensions Grid */}
      <div className="improved-grid">
        <div className="upload-card improved-concepts-card">
          <h3 className="card-subheading">
            <span className="card-icon">✨</span> Concepts Demonstrating Growth
          </h3>
          <p className="gaps-description">
            Specific areas where reassessment answers showed clearer reasoning and mechanism recall:
          </p>
          <div className="tags-container">
            {concepts_improved.length > 0 ? (
              concepts_improved.map((concept, cIdx) => (
                <span key={cIdx} className="improved-concept-tag">
                  ✓ {concept}
                </span>
              ))
            ) : (
              <span className="empty-tag">Foundational mechanics improved</span>
            )}
          </div>
        </div>

        <div className="upload-card improved-dimensions-card">
          <h3 className="card-subheading">
            <span className="card-icon">📈</span> Growth by Dimension
          </h3>
          <p className="gaps-description">
            Measured score deltas across diagnosed dimensions:
          </p>
          <div className="tags-container">
            {dimensions_improved.length > 0 ? (
              dimensions_improved.map((dimImp, dIdx) => (
                <span key={dIdx} className="improved-dimension-tag">
                  ▲ {dimImp}
                </span>
              ))
            ) : (
              <span className="empty-tag">Positive growth across assessed areas</span>
            )}
          </div>
        </div>
      </div>

      {/* Remaining Difficulties & Updated Recommendations */}
      <div className="future-steps-grid">
        <div className="upload-card remaining-diff-card">
          <h3 className="card-subheading">
            <span className="card-icon">🎯</span> Remaining Areas for Deliberate Practice
          </h3>
          <p className="gaps-description">
            Target these nuanced areas during your next study sessions:
          </p>
          <ul className="remaining-list">
            {remaining_difficulties.map((diff, diffIdx) => (
              <li key={diffIdx} className="remaining-item">
                {diff}
              </li>
            ))}
          </ul>
        </div>

        <div className="upload-card updated-recs-card">
          <h3 className="card-subheading">
            <span className="card-icon">💡</span> Updated Actionable Recommendations
          </h3>
          <p className="gaps-description">
            Next steps tailored to your current reassessment profile:
          </p>
          <ul className="updated-recs-list">
            {updated_recommendations.map((rec, rIdx) => (
              <li key={rIdx} className="updated-rec-item">
                {rec}
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Action Row */}
      <div className="action-row-split" style={{ marginTop: '2.5rem' }}>
        <button
          type="button"
          className="secondary-btn"
          onClick={onViewLearningMap}
        >
          ← Review Learning Map
        </button>

        <button
          type="button"
          className="primary-btn pulse-glow-btn"
          onClick={onRestart}
        >
          Start New Study Material Analysis ↻
        </button>
      </div>
    </div>
  )
}
