import { useState } from 'react'
import * as pdfjsLib from 'pdfjs-dist'
import './App.css'
import LearningMapView from './components/LearningMapView'
import DiagnosticAssessmentView from './components/DiagnosticAssessmentView'
import DiagnosisView from './components/DiagnosisView'
import InterventionView from './components/InterventionView'
import ReassessmentView from './components/ReassessmentView'
import BeforeAfterProfileView from './components/BeforeAfterProfileView'

// Configure pdfjs-dist worker correctly for Vite
pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url
).toString()

// Backend API URLs
const BACKEND_API_URL = 'http://localhost:8000/analyze-material'
const BACKEND_ASSESSMENT_URL = 'http://localhost:8000/generate-assessment'
const BACKEND_ANSWER_SHEET_URL = 'http://localhost:8000/analyze-answer-sheet'
const BACKEND_DIAGNOSE_URL = 'http://localhost:8000/diagnose'
const BACKEND_INTERVENTION_URL = 'http://localhost:8000/generate-intervention'
const BACKEND_REASSESSMENT_URL = 'http://localhost:8000/generate-reassessment'
const BACKEND_EVAL_REASSESSMENT_URL = 'http://localhost:8000/evaluate-reassessment'

function App() {
  // Step navigation:
  // 'study_material' | 'learning_map' | 'answer_sheet' | 'diagnostic_assessment' |
  // 'diagnosis' | 'intervention' | 'reassessment' | 'before_after_profile'
  const [currentStep, setCurrentStep] = useState('study_material')

  // --- Study Material State ---
  const [selectedFile, setSelectedFile] = useState(null)
  const [extractedText, setExtractedText] = useState('')
  const [statusMessage, setStatusMessage] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [processingStep, setProcessingStep] = useState('') // 'extracting' | 'analyzing' | ''
  const [errorMessage, setErrorMessage] = useState('')
  const [learningMap, setLearningMap] = useState(null)

  // --- Previous Answer Sheet State ---
  const [answerSheetFile, setAnswerSheetFile] = useState(null)
  const [answerSheetText, setAnswerSheetText] = useState('')
  const [answerSheetStatus, setAnswerSheetStatus] = useState('')
  const [answerSheetError, setAnswerSheetError] = useState('')
  const [isProcessingAnswerSheet, setIsProcessingAnswerSheet] = useState(false)
  const [answerSheetAnalysis, setAnswerSheetAnalysis] = useState(null)

  // --- Diagnostic Assessment State ---
  const [diagnosticQuestions, setDiagnosticQuestions] = useState([])
  const [isGeneratingAssessment, setIsGeneratingAssessment] = useState(false)
  const [assessmentStatus, setAssessmentStatus] = useState('')
  const [assessmentError, setAssessmentError] = useState('')
  const [submittedResponses, setSubmittedResponses] = useState([])

  // --- Learning Diagnosis State ---
  const [diagnosis, setDiagnosis] = useState(null)
  const [isDiagnosing, setIsDiagnosing] = useState(false)
  const [diagnosisError, setDiagnosisError] = useState('')

  // --- ONE Personalized Intervention State ---
  const [intervention, setIntervention] = useState(null)
  const [isGeneratingIntervention, setIsGeneratingIntervention] = useState(false)
  const [interventionError, setInterventionError] = useState('')

  // --- Targeted Reassessment State ---
  const [reassessmentQuestions, setReassessmentQuestions] = useState([])
  const [isGeneratingReassessment, setIsGeneratingReassessment] = useState(false)
  const [reassessmentError, setReassessmentError] = useState('')

  // --- Final Before/After Profile State ---
  const [beforeAfterProfile, setBeforeAfterProfile] = useState(null)
  const [isEvaluatingReassessment, setIsEvaluatingReassessment] = useState(false)
  const [profileError, setProfileError] = useState('')

  // Handle study material file selection
  const handleFileChange = (event) => {
    const file = event.target.files[0]
    setErrorMessage('')
    setStatusMessage('')

    if (!file) {
      setSelectedFile(null)
      return
    }

    if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
      setSelectedFile(null)
      setErrorMessage('Please select a valid PDF file.')
      return
    }

    setSelectedFile(file)
  }

  // Handle previous answer sheet file selection
  const handleAnswerSheetChange = (event) => {
    const file = event.target.files[0]
    setAnswerSheetError('')
    setAnswerSheetStatus('')

    if (!file) {
      setAnswerSheetFile(null)
      return
    }

    if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
      setAnswerSheetFile(null)
      setAnswerSheetError('Please select a valid PDF file for the answer sheet.')
      return
    }

    setAnswerSheetFile(file)
  }

  // Reset all state when user explicitly wants to upload new material
  const handleResetStudyMaterial = () => {
    setSelectedFile(null)
    setExtractedText('')
    setStatusMessage('')
    setErrorMessage('')
    setIsProcessing(false)
    setProcessingStep('')
    setLearningMap(null)
    setAnswerSheetFile(null)
    setAnswerSheetText('')
    setAnswerSheetStatus('')
    setAnswerSheetError('')
    setAnswerSheetAnalysis(null)
    setDiagnosticQuestions([])
    setIsGeneratingAssessment(false)
    setAssessmentStatus('')
    setAssessmentError('')
    setSubmittedResponses([])
    setDiagnosis(null)
    setIsDiagnosing(false)
    setDiagnosisError('')
    setIntervention(null)
    setIsGeneratingIntervention(false)
    setInterventionError('')
    setReassessmentQuestions([])
    setIsGeneratingReassessment(false)
    setReassessmentError('')
    setBeforeAfterProfile(null)
    setIsEvaluatingReassessment(false)
    setProfileError('')
    setCurrentStep('study_material')
  }

  // Extract text from study material PDF and analyze with FastAPI backend
  const handleProcessAndAnalyze = async () => {
    setErrorMessage('')
    setStatusMessage('')

    if (!selectedFile) {
      setErrorMessage('Please select a study material PDF file first before continuing.')
      return
    }

    setIsProcessing(true)
    setProcessingStep('extracting')
    setStatusMessage('Reading PDF and extracting text...')

    let fullText = ''

    try {
      const arrayBuffer = await selectedFile.arrayBuffer()
      const loadingTask = pdfjsLib.getDocument({ data: new Uint8Array(arrayBuffer) })
      const pdf = await loadingTask.promise

      for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {
        const page = await pdf.getPage(pageNum)
        const textContent = await page.getTextContent()
        const pageText = textContent.items
          .map((item) => ('str' in item ? item.str : ''))
          .join(' ')
        fullText += `--- Page ${pageNum} ---\n${pageText}\n\n`
      }

      if (!fullText.trim()) {
        throw new Error(
          'No readable text could be extracted from this PDF. Please ensure it contains selectable text rather than scanned images.'
        )
      }

      setExtractedText(fullText)
      console.log('--- Extracted Study Material PDF Text (Hidden from Webpage) ---')
      console.log(fullText)

      setProcessingStep('analyzing')
      setStatusMessage(
        `Extracted ${pdf.numPages} page(s). Analyzing material with AI to generate clean Learning Map...`
      )

      let response
      try {
        response = await fetch(BACKEND_API_URL, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            text: fullText,
            filename: selectedFile.name,
          }),
        })
      } catch (networkErr) {
        throw new Error(
          'Unable to connect to the FastAPI backend at http://localhost:8000. Please ensure the Python server is running.'
        )
      }

      const data = await response.json()

      if (!response.ok) {
        const errorDetail = data?.detail || data?.error || 'Failed to analyze study material.'
        throw new Error(errorDetail)
      }

      if (!data.success || !data.learning_map) {
        throw new Error('Malformed or incomplete response from the AI analyzer backend.')
      }

      setLearningMap(data.learning_map)
      setStatusMessage('Learning Map successfully generated from study material!')
      setCurrentStep('learning_map')
    } catch (error) {
      console.error('Processing error:', error)
      setErrorMessage(
        error.message || 'An error occurred while processing the PDF and analyzing study material.'
      )
    } finally {
      setIsProcessing(false)
      setProcessingStep('')
    }
  }

  // Extract text from the previous answer sheet PDF
  const handleReadAnswerSheet = async () => {
    setAnswerSheetError('')
    setAnswerSheetStatus('')

    if (!answerSheetFile) {
      setAnswerSheetError('Please select an answer sheet PDF file first.')
      return
    }

    setIsProcessingAnswerSheet(true)
    setAnswerSheetStatus('Reading answer sheet PDF and extracting text...')

    try {
      const arrayBuffer = await answerSheetFile.arrayBuffer()
      const loadingTask = pdfjsLib.getDocument({ data: new Uint8Array(arrayBuffer) })
      const pdf = await loadingTask.promise

      let fullText = ''
      for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {
        const page = await pdf.getPage(pageNum)
        const textContent = await page.getTextContent()
        const pageText = textContent.items
          .map((item) => ('str' in item ? item.str : ''))
          .join(' ')
        fullText += `--- Page ${pageNum} ---\n${pageText}\n\n`
      }

      if (!fullText.trim()) {
        throw new Error(
          'No readable text could be extracted from this answer sheet. Please ensure it contains selectable text.'
        )
      }

      setAnswerSheetText(fullText)
      console.log('--- Extracted Answer Sheet Text (Hidden from Webpage) ---')
      console.log(fullText)

      setAnswerSheetStatus(
        `Successfully extracted ${pdf.numPages} page(s) from answer sheet. Preserved for learning diagnosis.`
      )
    } catch (error) {
      console.error('Error reading answer sheet:', error)
      setAnswerSheetError(
        error.message || 'Failed to read the answer sheet PDF. Please ensure it is a readable PDF.'
      )
    } finally {
      setIsProcessingAnswerSheet(false)
    }
  }

  // Generate Diagnostic Assessment using Learning Map, Study Material, and optional Answer Sheet
  const handleGenerateAssessment = async () => {
    setAssessmentError('')
    setAssessmentStatus('Preparing diagnostic assessment...')
    setIsGeneratingAssessment(true)
    setCurrentStep('diagnostic_assessment')

    try {
      let sheetAnalysis = answerSheetAnalysis
      let sheetText = answerSheetText

      if (!sheetText && answerSheetFile) {
        try {
          const arrayBuffer = await answerSheetFile.arrayBuffer()
          const loadingTask = pdfjsLib.getDocument({ data: new Uint8Array(arrayBuffer) })
          const pdf = await loadingTask.promise
          let fullText = ''
          for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {
            const page = await pdf.getPage(pageNum)
            const textContent = await page.getTextContent()
            const pageText = textContent.items
              .map((item) => ('str' in item ? item.str : ''))
              .join(' ')
            fullText += `--- Page ${pageNum} ---\n${pageText}\n\n`
          }
          if (fullText.trim()) {
            sheetText = fullText
            setAnswerSheetText(fullText)
          }
        } catch (readErr) {
          console.warn('Could not auto-extract answer sheet text:', readErr)
        }
      }

      if (sheetText && sheetText.trim() && !sheetAnalysis) {
        try {
          setAssessmentStatus('Analyzing previous answer sheet evidence...')
          const sheetRes = await fetch(BACKEND_ANSWER_SHEET_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              text: sheetText,
              filename: answerSheetFile ? answerSheetFile.name : undefined,
              learning_map: learningMap,
            }),
          })
          if (sheetRes.ok) {
            const sheetData = await sheetRes.json()
            if (sheetData.success && sheetData.analysis) {
              sheetAnalysis = sheetData.analysis
              setAnswerSheetAnalysis(sheetAnalysis)
            }
          }
        } catch (sheetErr) {
          console.warn('Could not analyze answer sheet:', sheetErr)
        }
      }

      setAssessmentStatus('Generating diagnostic questions grounded in your study material...')
      const response = await fetch(BACKEND_ASSESSMENT_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          learning_map: learningMap,
          study_material_text: extractedText,
          answer_sheet_analysis: sheetAnalysis || undefined,
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        const errorDetail = data?.detail || data?.error || 'Failed to generate diagnostic assessment.'
        throw new Error(errorDetail)
      }

      if (!data.success || !data.questions || data.questions.length === 0) {
        throw new Error('Malformed or empty response from diagnostic assessment generator.')
      }

      setDiagnosticQuestions(data.questions)
      setAssessmentStatus(`Generated ${data.questions.length} diagnostic questions successfully!`)
    } catch (error) {
      console.error('Error generating diagnostic assessment:', error)
      setAssessmentError(error.message || 'Failed to generate diagnostic assessment.')
    } finally {
      setIsGeneratingAssessment(false)
    }
  }

  // Handle student answers submission -> Trigger Learning Diagnosis
  const handleSubmitAssessment = async (responses) => {
    setSubmittedResponses(responses)
    setIsDiagnosing(true)
    setDiagnosisError('')
    setCurrentStep('diagnosis')

    try {
      const response = await fetch(BACKEND_DIAGNOSE_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          learning_map: learningMap,
          questions: diagnosticQuestions,
          student_answers: responses,
          answer_sheet_analysis: answerSheetAnalysis || undefined,
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data?.detail || data?.error || 'Failed to diagnose learning patterns.')
      }

      if (!data.success || !data.diagnosis) {
        throw new Error('Malformed diagnosis response from backend.')
      }

      setDiagnosis(data.diagnosis)
    } catch (err) {
      console.error('Diagnosis error:', err)
      setDiagnosisError(err.message || 'Error synthesizing learning diagnosis.')
    } finally {
      setIsDiagnosing(false)
    }
  }

  // Generate ONE Unified Personalized Intervention targeting student's weakest dimensions
  const handleGenerateIntervention = async () => {
    if (!diagnosis) return
    setIsGeneratingIntervention(true)
    setInterventionError('')
    setCurrentStep('intervention')

    try {
      const response = await fetch(BACKEND_INTERVENTION_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          diagnosis,
          learning_map: learningMap,
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data?.detail || data?.error || 'Failed to generate personalized intervention.')
      }

      if (!data.success || !data.intervention) {
        throw new Error('Malformed intervention response from backend.')
      }

      setIntervention(data.intervention)
    } catch (err) {
      console.error('Intervention generation error:', err)
      setInterventionError(err.message || 'Error generating personalized intervention.')
    } finally {
      setIsGeneratingIntervention(false)
    }
  }

  // Generate Targeted Reassessment Questions
  const handleGenerateReassessment = async () => {
    if (!diagnosis) return
    setIsGeneratingReassessment(true)
    setReassessmentError('')
    setCurrentStep('reassessment')

    try {
      const response = await fetch(BACKEND_REASSESSMENT_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          diagnosis,
          learning_map: learningMap,
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data?.detail || data?.error || 'Failed to generate targeted reassessment.')
      }

      if (!data.success || !data.questions || data.questions.length === 0) {
        throw new Error('Malformed reassessment response from backend.')
      }

      setReassessmentQuestions(data.questions)
    } catch (err) {
      console.error('Reassessment generation error:', err)
      setReassessmentError(err.message || 'Error generating targeted reassessment.')
    } finally {
      setIsGeneratingReassessment(false)
    }
  }

  // Evaluate Reassessment Answers -> Generate Before vs After Learning Profile
  const handleSubmitReassessment = async (responses) => {
    if (!diagnosis) return
    setIsEvaluatingReassessment(true)
    setProfileError('')
    setCurrentStep('before_after_profile')

    try {
      const response = await fetch(BACKEND_EVAL_REASSESSMENT_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          before_scores: diagnosis.dimension_averages,
          questions: reassessmentQuestions,
          student_answers: responses,
          diagnosis,
          learning_map: learningMap,
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data?.detail || data?.error || 'Failed to evaluate reassessment.')
      }

      if (!data.success || !data.profile) {
        throw new Error('Malformed profile response from backend.')
      }

      setBeforeAfterProfile(data.profile)
    } catch (err) {
      console.error('Reassessment evaluation error:', err)
      setProfileError(err.message || 'Error evaluating reassessment.')
    } finally {
      setIsEvaluatingReassessment(false)
    }
  }

  return (
    <div className="app-container">
      <header className="header">
        <h1 className="title">AI Study Weakness Detector</h1>
        <p className="subtitle">Discover what you're struggling with — and why.</p>

        {/* Step Navigation Bar */}
        <nav className="step-nav" aria-label="Workflow progress">
          <button
            type="button"
            className={`step-btn ${currentStep === 'study_material' ? 'active' : ''} ${
              learningMap ? 'completed' : ''
            }`}
            onClick={() => setCurrentStep('study_material')}
          >
            <span className="step-number">1</span>
            <span className="step-text">Study Material</span>
          </button>

          <span className="step-arrow">→</span>

          <button
            type="button"
            className={`step-btn ${currentStep === 'learning_map' ? 'active' : ''} ${
              learningMap ? 'completed' : 'disabled'
            }`}
            onClick={() => learningMap && setCurrentStep('learning_map')}
            disabled={!learningMap}
          >
            <span className="step-number">2</span>
            <span className="step-text">Learning Map</span>
          </button>

          <span className="step-arrow">→</span>

          <button
            type="button"
            className={`step-btn ${currentStep === 'answer_sheet' ? 'active' : ''} ${
              answerSheetAnalysis ? 'completed' : !learningMap ? 'disabled' : ''
            }`}
            onClick={() => learningMap && setCurrentStep('answer_sheet')}
            disabled={!learningMap}
          >
            <span className="step-number">3</span>
            <span className="step-text">Answer Sheet</span>
          </button>

          <span className="step-arrow">→</span>

          <button
            type="button"
            className={`step-btn ${currentStep === 'diagnostic_assessment' ? 'active' : ''} ${
              diagnosis ? 'completed' : !learningMap ? 'disabled' : ''
            }`}
            onClick={() => {
              if (learningMap) {
                if (diagnosticQuestions.length > 0) {
                  setCurrentStep('diagnostic_assessment')
                } else {
                  handleGenerateAssessment()
                }
              }
            }}
            disabled={!learningMap}
          >
            <span className="step-number">4</span>
            <span className="step-text">Diagnostic Test</span>
          </button>

          <span className="step-arrow">→</span>

          <button
            type="button"
            className={`step-btn ${currentStep === 'diagnosis' ? 'active' : ''} ${
              intervention ? 'completed' : !diagnosis ? 'disabled' : ''
            }`}
            onClick={() => diagnosis && setCurrentStep('diagnosis')}
            disabled={!diagnosis}
          >
            <span className="step-number">5</span>
            <span className="step-text">Diagnosis</span>
          </button>

          <span className="step-arrow">→</span>

          <button
            type="button"
            className={`step-btn ${currentStep === 'intervention' ? 'active' : ''} ${
              beforeAfterProfile ? 'completed' : !intervention ? 'disabled' : ''
            }`}
            onClick={() => intervention && setCurrentStep('intervention')}
            disabled={!intervention}
          >
            <span className="step-number">6</span>
            <span className="step-text">Intervention</span>
          </button>

          <span className="step-arrow">→</span>

          <button
            type="button"
            className={`step-btn ${currentStep === 'reassessment' ? 'active' : ''} ${
              beforeAfterProfile ? 'completed' : !reassessmentQuestions.length ? 'disabled' : ''
            }`}
            onClick={() => reassessmentQuestions.length && setCurrentStep('reassessment')}
            disabled={!reassessmentQuestions.length}
          >
            <span className="step-number">7</span>
            <span className="step-text">Reassessment</span>
          </button>

          <span className="step-arrow">→</span>

          <button
            type="button"
            className={`step-btn ${currentStep === 'before_after_profile' ? 'active' : ''} ${
              !beforeAfterProfile ? 'disabled' : ''
            }`}
            onClick={() => beforeAfterProfile && setCurrentStep('before_after_profile')}
            disabled={!beforeAfterProfile}
          >
            <span className="step-number">8</span>
            <span className="step-text">Profile Growth</span>
          </button>
        </nav>
      </header>

      <main className="main-content">
        {/* STEP 1: Upload Study Material */}
        {currentStep === 'study_material' && (
          <div className="upload-card">
            <section className="upload-section">
              <div className="section-header-row">
                <h2 className="section-title">Upload Study Material</h2>
                {learningMap && (
                  <button
                    type="button"
                    className="view-link-btn"
                    onClick={() => setCurrentStep('learning_map')}
                  >
                    View Current Learning Map →
                  </button>
                )}
              </div>
              <p className="section-description">
                Upload your study material (such as notes, textbook chapters, or syllabus) in PDF format.
                The AI will extract and structure your material into a clean Learning Map without document metadata noise.
              </p>

              <div className="file-input-wrapper">
                <label htmlFor="pdf-upload" className="file-drop-area">
                  <svg
                    className="upload-icon"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                    />
                  </svg>
                  <span className="file-label-text">
                    Choose a PDF file or click to browse
                  </span>
                  <span className="file-hint">Only .pdf files are supported</span>
                </label>

                <input
                  id="pdf-upload"
                  type="file"
                  accept=".pdf,application/pdf"
                  onChange={handleFileChange}
                  className="file-input"
                  disabled={isProcessing}
                />
              </div>

              {selectedFile && (
                <div className="selected-file-badge">
                  <span className="file-badge-icon">📄</span>
                  <span className="file-badge-name">{selectedFile.name}</span>
                  <span className="file-badge-size">
                    ({(selectedFile.size / 1024).toFixed(1)} KB)
                  </span>
                </div>
              )}

              {errorMessage && (
                <div className="alert-message error-message" role="alert">
                  <strong>Error: </strong> {errorMessage}
                </div>
              )}

              {statusMessage && (
                <div className="alert-message success-message" role="status">
                  {isProcessing && <span className="inline-spinner" aria-hidden="true" />}
                  {statusMessage}
                </div>
              )}

              <div className="action-row">
                <button
                  type="button"
                  className="primary-btn"
                  onClick={handleProcessAndAnalyze}
                  disabled={isProcessing || !selectedFile}
                >
                  {isProcessing
                    ? processingStep === 'extracting'
                      ? 'Extracting PDF Text...'
                      : 'Analyzing with AI...'
                    : 'Analyze Study Material'}
                </button>
              </div>
            </section>
          </div>
        )}

        {/* STEP 2: Structured Learning Map Display */}
        {currentStep === 'learning_map' && learningMap && (
          <LearningMapView
            learningMap={learningMap}
            onProceedToAnswerSheet={() => setCurrentStep('answer_sheet')}
            onProceedToAssessment={handleGenerateAssessment}
            onResetStudyMaterial={handleResetStudyMaterial}
          />
        )}

        {/* STEP 3: Previous Answer Sheet Flow */}
        {currentStep === 'answer_sheet' && (
          <div className="upload-card answer-sheet-card">
            <section className="upload-section">
              <div className="section-header-row">
                <div>
                  <span className="step-badge">Step 3 (Optional)</span>
                  <h2 className="section-title">Upload Previous Answer Sheet</h2>
                </div>
                <button
                  type="button"
                  className="view-link-btn"
                  onClick={() => setCurrentStep('learning_map')}
                >
                  ← Back to Learning Map
                </button>
              </div>

              <p className="section-description">
                Upload a previous exam, quiz, or test answer sheet in PDF format.
                This will be preserved alongside your Learning Map to provide additional evidence for learning diagnosis.
              </p>

              <div className="file-input-wrapper">
                <label htmlFor="answer-sheet-upload" className="file-drop-area answer-sheet-drop-area">
                  <svg
                    className="upload-icon answer-sheet-icon"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                  </svg>
                  <span className="file-label-text">
                    Choose an Answer Sheet PDF or click to browse
                  </span>
                  <span className="file-hint">Upload previous test or marked answer sheet (.pdf)</span>
                </label>

                <input
                  id="answer-sheet-upload"
                  type="file"
                  accept=".pdf,application/pdf"
                  onChange={handleAnswerSheetChange}
                  className="file-input"
                  disabled={isProcessingAnswerSheet}
                />
              </div>

              {answerSheetFile && (
                <div className="selected-file-badge answer-sheet-badge">
                  <span className="file-badge-icon">📝</span>
                  <span className="file-badge-name">{answerSheetFile.name}</span>
                  <span className="file-badge-size">
                    ({(answerSheetFile.size / 1024).toFixed(1)} KB)
                  </span>
                </div>
              )}

              {answerSheetError && (
                <div className="alert-message error-message" role="alert">
                  <strong>Error: </strong> {answerSheetError}
                </div>
              )}

              {answerSheetStatus && (
                <div className="alert-message success-message" role="status">
                  {isProcessingAnswerSheet && <span className="inline-spinner" aria-hidden="true" />}
                  {answerSheetStatus}
                </div>
              )}

              <div className="action-row-split">
                <button
                  type="button"
                  className="secondary-btn"
                  onClick={() => setCurrentStep('learning_map')}
                >
                  ← Back to Learning Map
                </button>

                <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
                  <button
                    type="button"
                    className="secondary-btn"
                    onClick={handleReadAnswerSheet}
                    disabled={isProcessingAnswerSheet || !answerSheetFile}
                  >
                    {isProcessingAnswerSheet ? 'Reading Answer Sheet...' : 'Process Answer Sheet'}
                  </button>

                  <button
                    type="button"
                    className="primary-btn"
                    onClick={handleGenerateAssessment}
                    disabled={isProcessingAnswerSheet || isGeneratingAssessment}
                  >
                    {isGeneratingAssessment
                      ? 'Generating Questions...'
                      : answerSheetText
                      ? 'Proceed to Diagnostic Assessment →'
                      : 'Skip Answer Sheet → Diagnostic Assessment'}
                  </button>
                </div>
              </div>
            </section>
          </div>
        )}

        {/* STEP 4: Diagnostic Assessment View */}
        {currentStep === 'diagnostic_assessment' && (
          <>
            {isGeneratingAssessment && (
              <div className="upload-card assessment-loading-card">
                <div className="loading-content">
                  <span className="inline-spinner large-spinner" />
                  <h3 className="loading-title">Generating Diagnostic Assessment</h3>
                  <p className="loading-desc">
                    Analyzing your Learning Map and study material to curate 6-8 diagnostic questions across all 4 learning dimensions...
                  </p>
                </div>
              </div>
            )}

            {!isGeneratingAssessment && assessmentError && (
              <div className="upload-card">
                <div className="alert-message error-message" role="alert">
                  <strong>Error: </strong> {assessmentError}
                </div>
                <div className="action-row-split" style={{ marginTop: '1.5rem' }}>
                  <button
                    type="button"
                    className="secondary-btn"
                    onClick={() => setCurrentStep('learning_map')}
                  >
                    ← Back to Learning Map
                  </button>
                  <button
                    type="button"
                    className="primary-btn"
                    onClick={handleGenerateAssessment}
                  >
                    Retry Generation
                  </button>
                </div>
              </div>
            )}

            {!isGeneratingAssessment && !assessmentError && diagnosticQuestions.length > 0 && (
              <DiagnosticAssessmentView
                questions={diagnosticQuestions}
                onSubmitAnswers={handleSubmitAssessment}
                onBack={() => setCurrentStep('learning_map')}
                isDiagnosing={isDiagnosing}
              />
            )}
          </>
        )}

        {/* STEP 5: Learning Diagnosis View */}
        {currentStep === 'diagnosis' && (
          <>
            {isDiagnosing && (
              <div className="upload-card assessment-loading-card">
                <div className="loading-content">
                  <span className="inline-spinner large-spinner" />
                  <h3 className="loading-title">Synthesizing Learning Diagnosis</h3>
                  <p className="loading-desc">
                    Evaluating your answers against question-specific rubrics across Concept Understanding,
                    Logical Reasoning, Problem Solving, and Practical Application...
                  </p>
                </div>
              </div>
            )}

            {!isDiagnosing && diagnosisError && (
              <div className="upload-card">
                <div className="alert-message error-message" role="alert">
                  <strong>Error: </strong> {diagnosisError}
                </div>
                <div className="action-row-split" style={{ marginTop: '1.5rem' }}>
                  <button
                    type="button"
                    className="secondary-btn"
                    onClick={() => setCurrentStep('diagnostic_assessment')}
                  >
                    ← Back to Questions
                  </button>
                  <button
                    type="button"
                    className="primary-btn"
                    onClick={() => handleSubmitAssessment(submittedResponses)}
                  >
                    Retry Diagnosis
                  </button>
                </div>
              </div>
            )}

            {!isDiagnosing && !diagnosisError && diagnosis && (
              <DiagnosisView
                diagnosis={diagnosis}
                learningMap={learningMap}
                onProceedToIntervention={handleGenerateIntervention}
                onBackToMap={() => setCurrentStep('learning_map')}
                isGeneratingIntervention={isGeneratingIntervention}
              />
            )}
          </>
        )}

        {/* STEP 6: ONE Unified Personalized Intervention */}
        {currentStep === 'intervention' && (
          <>
            {isGeneratingIntervention && (
              <div className="upload-card assessment-loading-card">
                <div className="loading-content">
                  <span className="inline-spinner large-spinner" />
                  <h3 className="loading-title">Generating Personalized Intervention</h3>
                  <p className="loading-desc">
                    Synthesizing diagnosed gaps into ONE targeted study pathway specifically addressing your weakest dimensions...
                  </p>
                </div>
              </div>
            )}

            {!isGeneratingIntervention && interventionError && (
              <div className="upload-card">
                <div className="alert-message error-message" role="alert">
                  <strong>Error: </strong> {interventionError}
                </div>
                <div className="action-row-split" style={{ marginTop: '1.5rem' }}>
                  <button
                    type="button"
                    className="secondary-btn"
                    onClick={() => setCurrentStep('diagnosis')}
                  >
                    ← Back to Diagnosis
                  </button>
                  <button
                    type="button"
                    className="primary-btn"
                    onClick={handleGenerateIntervention}
                  >
                    Retry Intervention Generation
                  </button>
                </div>
              </div>
            )}

            {!isGeneratingIntervention && !interventionError && intervention && (
              <InterventionView
                intervention={intervention}
                learningMap={learningMap}
                onProceedToReassessment={handleGenerateReassessment}
                onBackToDiagnosis={() => setCurrentStep('diagnosis')}
                isGeneratingReassessment={isGeneratingReassessment}
              />
            )}
          </>
        )}

        {/* STEP 7: Targeted Reassessment */}
        {currentStep === 'reassessment' && (
          <>
            {isGeneratingReassessment && (
              <div className="upload-card assessment-loading-card">
                <div className="loading-content">
                  <span className="inline-spinner large-spinner" />
                  <h3 className="loading-title">Preparing Targeted Reassessment</h3>
                  <p className="loading-desc">
                    Creating 3-4 comparable questions targeting your diagnosed weak areas to verify mastery gains...
                  </p>
                </div>
              </div>
            )}

            {!isGeneratingReassessment && reassessmentError && (
              <div className="upload-card">
                <div className="alert-message error-message" role="alert">
                  <strong>Error: </strong> {reassessmentError}
                </div>
                <div className="action-row-split" style={{ marginTop: '1.5rem' }}>
                  <button
                    type="button"
                    className="secondary-btn"
                    onClick={() => setCurrentStep('intervention')}
                  >
                    ← Back to Intervention
                  </button>
                  <button
                    type="button"
                    className="primary-btn"
                    onClick={handleGenerateReassessment}
                  >
                    Retry Reassessment Generation
                  </button>
                </div>
              </div>
            )}

            {!isGeneratingReassessment && !reassessmentError && reassessmentQuestions.length > 0 && (
              <ReassessmentView
                questions={reassessmentQuestions}
                onSubmitAnswers={handleSubmitReassessment}
                onBackToIntervention={() => setCurrentStep('intervention')}
                isEvaluating={isEvaluatingReassessment}
              />
            )}
          </>
        )}

        {/* STEP 8: Final Before vs After Learning Profile */}
        {currentStep === 'before_after_profile' && (
          <>
            {isEvaluatingReassessment && (
              <div className="upload-card assessment-loading-card">
                <div className="loading-content">
                  <span className="inline-spinner large-spinner" />
                  <h3 className="loading-title">Evaluating Reassessment Performance</h3>
                  <p className="loading-desc">
                    Comparing Before vs After performance across all 4 learning dimensions and calculating delta growth...
                  </p>
                </div>
              </div>
            )}

            {!isEvaluatingReassessment && profileError && (
              <div className="upload-card">
                <div className="alert-message error-message" role="alert">
                  <strong>Error: </strong> {profileError}
                </div>
                <div className="action-row-split" style={{ marginTop: '1.5rem' }}>
                  <button
                    type="button"
                    className="secondary-btn"
                    onClick={() => setCurrentStep('reassessment')}
                  >
                    ← Back to Reassessment
                  </button>
                </div>
              </div>
            )}

            {!isEvaluatingReassessment && !profileError && beforeAfterProfile && (
              <BeforeAfterProfileView
                profile={beforeAfterProfile}
                learningMap={learningMap}
                onRestart={handleResetStudyMaterial}
                onViewLearningMap={() => setCurrentStep('learning_map')}
              />
            )}
          </>
        )}
      </main>
    </div>
  )
}

export default App
