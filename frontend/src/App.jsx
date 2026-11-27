
import { useEffect, useRef, useState } from 'react'
import './App.css'

/* ========================================
   CONFIGURATION
   ======================================== */

const MAX_DOCUMENT_LENGTH = 50000
const MAX_FILE_SIZE = 25 * 1024 * 1024

const API_URL =
  import.meta.env.VITE_API_URL ||
  'http://127.0.0.1:8000/api/analyze'

/* ========================================
   FICTIONAL SAMPLE CONTRACT
   ======================================== */

const SAMPLE_CONTRACT = `Rental Agreement — fictional demonstration only

1. Monthly rent: The tenant shall pay INR 15,000 by the fifth day of each month.

2. Security deposit: The tenant shall pay INR 45,000. The owner may deduct any amount at their sole discretion without providing an itemized statement.

3. Termination: The owner may terminate this agreement without prior notice.

4. Late payment: INR 500 per day shall be charged for overdue rent, with no stated maximum.

5. Duration: Twelve months. The tenant is responsible for routine maintenance.`

const DEMO_FINDINGS = [
  {
    id: 'deposit',
    label: 'Clarify deductions',
    heading: 'Security deposit',
    section: 'Section 02 — Security deposit',
    before: 'The tenant shall pay INR 45,000. The owner may ',
    highlight: 'deduct any amount at their sole discretion',
    after: ' without providing an itemized statement.',
    note: 'Ask for an itemized list of deductions and a clear refund deadline.',
    tone: 'review',
    icon: '?'
  },
  {
    id: 'termination',
    label: 'Potential risk',
    heading: 'Termination',
    section: 'Section 03 — Termination',
    before: 'The owner may ',
    highlight: 'terminate this agreement without prior notice.',
    after: '',
    note: 'Ask whether a reasonable notice period and clear termination conditions can be included.',
    tone: 'risk',
    icon: '!'
  }
]

/* ========================================
   BRAND LOGO
   ======================================== */

function BrandMark() {
  return (
    <span className="brand-mark">
      <svg viewBox="0 0 32 32" fill="none" aria-hidden="true">
        <path
          d="M9 4.5h10l5 5V27H9V4.5Z"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinejoin="round"
        />

        <path
          d="M19 4.5v6h5M13 16h7M13 20h7M13 24h4"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
        />
      </svg>
    </span>
  )
}

/* ========================================
   SINGLE-DIRECTION FLOATING BUTTON
   ======================================== */

function MagneticButton({
  children,
  className = '',
  ...props
}) {
  return (
    <span
      className={`magnetic-zone ${
        className.includes('submit-button')
          ? 'magnetic-zone-wide'
          : ''
      }`}
    >
      <button
        type="button"
        {...props}
        className={`magnetic-button ${className}`}
      >
        <span className="button-surface">
          {children}
        </span>
      </button>
    </span>
  )
}

/* ========================================
   ANIMATED RISK SCORE
   ======================================== */

function AnimatedScore({ value }) {
  const [display, setDisplay] = useState(0)

  useEffect(() => {
    let frame
    let started

    const reduced = window.matchMedia(
      '(prefers-reduced-motion: reduce)'
    ).matches

    function tick(now) {
      started ??= now

      const progress = reduced
        ? 1
        : Math.min((now - started) / 850, 1)

      setDisplay(
        Math.round(value * (1 - (1 - progress) ** 3))
      )

      if (progress < 1) {
        frame = requestAnimationFrame(tick)
      }
    }

    frame = requestAnimationFrame(tick)

    return () => cancelAnimationFrame(frame)
  }, [value])

  return <strong aria-hidden="true">{display}</strong>
}

/* ========================================
   INTERACTIVE CONTRACT PREVIEW
   ======================================== */

function ContractPreview({ selected, onSelect }) {
  const current =
    DEMO_FINDINGS.find(item => item.id === selected) ||
    DEMO_FINDINGS[0]

  return (
    <div
      className="hero-art"
      aria-label="Interactive fictional contract preview"
    >
      <div className="preview-halo" aria-hidden="true" />

      <div className="document-card">

        <div className="document-topline">

          <span className="document-icon">▤</span>

          <span className="document-status">
            INTERACTIVE DOCUMENT PREVIEW
          </span>

          <span className="demo-pill">
            <i /> Fictional sample
          </span>

        </div>

        <div className="document-title">

          <div>
            <span className="tiny-label">
              AGREEMENT / 001
            </span>

            <h2>Rental Agreement</h2>
          </div>

          <span className="document-subtitle">
            Key terms worth understanding.
          </span>

        </div>

        {DEMO_FINDINGS.map(item => (

          <div className="preview-clause" key={item.id}>

            <span className="clause-section">
              {item.section}
            </span>

            <p>
              {item.before}

              <button
                type="button"
                className={`clause-highlight highlight-${item.tone}`}
                aria-pressed={selected === item.id}
                onClick={() => onSelect(item.id)}
              >
                {item.highlight}
              </button>

              {item.after}
            </p>

          </div>

        ))}

        <div
          className="preview-explanation"
          aria-live="polite"
        >

          <span className={`annotation-icon ${current.tone}`}>
            {current.icon}
          </span>

          <div>
            <strong>
              {current.label} · {current.heading}
            </strong>

            <p>{current.note}</p>
          </div>

        </div>

        <div className="document-footer">

          <span>✳</span>

          Your document, decoded.

          <span className="preview-instruction">
            Select a highlighted clause to explore ↗
          </span>

        </div>

      </div>

      {DEMO_FINDINGS.map((item, index) => (

        <button
          key={item.id}
          type="button"
          className={`floating-label float-${index} ${
            selected === item.id ? 'is-selected' : ''
          }`}
          aria-pressed={selected === item.id}
          onClick={() => onSelect(item.id)}
        >

          <span className={`annotation-icon ${item.tone}`}>
            {item.icon}
          </span>

          <span>

            <strong>{item.label}</strong>

            <small>
              {index === 0
                ? 'Review refund terms'
                : 'Review notice conditions'}
            </small>

          </span>

          <span className="annotation-arrow">↗</span>

        </button>

      ))}

    </div>
  )
}

/* ========================================
   MAIN APPLICATION
   ======================================== */

function App() {

  const [documentText, setDocumentText] = useState('')
  const [inputMode, setInputMode] = useState('upload')
const [uploadedText, setUploadedText] = useState('')
  const [documentType, setDocumentType] = useState('')

  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [cooldown, setCooldown] = useState(0)

  /* DOCUMENT UPLOAD STATES */

  const [uploading, setUploading] = useState(false)
  const [uploadInfo, setUploadInfo] = useState(null)
  const [uploadError, setUploadError] = useState('')

  const [selectedPreview, setSelectedPreview] =
    useState('deposit')

  const fileInputRef = useRef(null)
  const busyRef = useRef(false)
  const appRef = useRef(null)
  const auroraFrame = useRef(0)

  /* ========================================
     SCROLL REVEAL
     ======================================== */

  useEffect(() => {

    const root = appRef.current

    if (
      !root ||
      !('IntersectionObserver' in window) ||
      window.matchMedia(
        '(prefers-reduced-motion: reduce)'
      ).matches
    ) return

    const observer = new IntersectionObserver(
      entries => {
        entries.forEach(entry => {

          if (entry.isIntersecting) {
            entry.target.classList.add('revealed')
            observer.unobserve(entry.target)
          }

        })
      },
      { threshold: 0.08 }
    )

    root.querySelectorAll('.reveal').forEach(node => {
      observer.observe(node)
    })

    return () => observer.disconnect()

  }, [])

  useEffect(() => {
    return () => cancelAnimationFrame(auroraFrame.current)
  }, [])

  /* ========================================
     CURSOR RESPONSIVE AURORA
     ======================================== */

  function moveAurora(event) {

    if (
      event.pointerType !== 'mouse' ||
      !window.matchMedia(
        '(hover: hover) and (pointer: fine) and (prefers-reduced-motion: no-preference)'
      ).matches
    ) return

    const section = event.currentTarget
    const rect = section.getBoundingClientRect()

    const { clientX, clientY } = event

    const x = (clientX - rect.left) / rect.width * 100
    const y = (clientY - rect.top) / rect.height * 100

    cancelAnimationFrame(auroraFrame.current)

    auroraFrame.current = requestAnimationFrame(() => {

      section.style.setProperty('--glow-x', `${x}%`)
      section.style.setProperty('--glow-y', `${y}%`)

      const preview = section.querySelector('.hero-art')
      const bounds = preview?.getBoundingClientRect()

      const inside =
        bounds &&
        clientX >= bounds.left &&
        clientX <= bounds.right &&
        clientY >= bounds.top &&
        clientY <= bounds.bottom

      section.style.setProperty(
        '--tilt-x',
        inside
          ? `${(0.5 - (clientY - bounds.top) / bounds.height) * 2.4}deg`
          : '0deg'
      )

      section.style.setProperty(
        '--tilt-y',
        inside
          ? `${((clientX - bounds.left) / bounds.width - 0.5) * 2.4}deg`
          : '0deg'
      )

    })
  }

  function resetAurora(event) {

    cancelAnimationFrame(auroraFrame.current)

    event.currentTarget.style.setProperty('--tilt-x', '0deg')
    event.currentTarget.style.setProperty('--tilt-y', '0deg')

  }

  /* ========================================
     SCROLL TO ANALYZER
     ======================================== */

  function scrollToAnalyzer() {

    document.getElementById('analyzer')?.scrollIntoView({

      behavior: window.matchMedia(
        '(prefers-reduced-motion: reduce)'
      ).matches ? 'instant' : 'smooth'

    })

  }

  /* ========================================
     LOAD FICTIONAL SAMPLE
     ======================================== */
     const activeText =
  inputMode === 'upload'
    ? uploadedText
    : documentText

function changeInputMode(mode) {
  if (
    busyRef.current ||
    loading ||
    uploading ||
    mode === inputMode
  ) return

  setInputMode(mode)
  setDocumentType('')
  setResult(null)
  setError('')
  setUploadError('')
}

 function loadSample() {
  if (busyRef.current || loading || uploading) return

  if (
    documentText.trim() &&
    documentText !== SAMPLE_CONTRACT &&
    !window.confirm(
      'Replace your pasted text with the fictional sample?'
    )
  ) return

  setInputMode('paste')
  setDocumentType('rental_agreement')
  setDocumentText(SAMPLE_CONTRACT)

  setUploadError('')
  setError('')
  setResult(null)

  scrollToAnalyzer()
}

  /* ========================================
     DOCUMENT UPLOAD AND EXTRACTION
     ======================================== */


async function uploadDocument(file) {
  if (
    !file ||
    busyRef.current ||
    uploading ||
    loading
  ) return

  setUploadError('')


  /* FILE TYPE VALIDATION */

  if (!/\.(pdf|docx|txt)$/i.test(file.name)) {
    setUploadError(
      'Please upload a PDF, DOCX or TXT file.'
    )
    return
  }

  /* FILE SIZE VALIDATION */

  if (file.size === 0) {
    setUploadError('The selected file is empty.')
    return
  }

  if (file.size > MAX_FILE_SIZE) {
    setUploadError(
      'Maximum supported file size is 25 MB.'
    )
    return
  }

  /* CONFIRM REPLACEMENT */

  if (
    uploadedText.trim() &&
    !window.confirm(
      'Replace the previously uploaded document?'
    )
  ) return

  busyRef.current = true
  setUploading(true)

  try {

    /* CREATE MULTIPART REQUEST */

    const formData = new FormData()

    formData.append('file', file)

    /* DETERMINE EXTRACTION ENDPOINT */

    const analyzeUrl = new URL(
      API_URL,
      window.location.origin
    )

    let extractUrl = import.meta.env.VITE_EXTRACT_URL

    if (!extractUrl) {

      if (!/\/analyze\/?$/.test(analyzeUrl.pathname)) {
        throw new Error(
          'Configure VITE_EXTRACT_URL for document extraction.'
        )
      }

      analyzeUrl.pathname = analyzeUrl.pathname.replace(
        /\/analyze\/?$/,
        '/extract'
      )

      analyzeUrl.search = ''
      analyzeUrl.hash = ''

      extractUrl = analyzeUrl.toString()
    }

    /* SEND DOCUMENT TO BACKEND */

    const response = await fetch(extractUrl, {
      method: 'POST',
      body: formData
    })

    const data = await response.json().catch(() => null)

    /* HANDLE BACKEND ERRORS */

    if (!response.ok) {

      const detail = data?.detail

      throw new Error(
        typeof detail === 'string'
          ? detail
          : detail?.message ||
            `Document extraction failed (HTTP ${response.status}).`
      )
    }

    /* VALIDATE EXTRACTED TEXT */

    if (
      typeof data?.full_text !== 'string' ||
      !data.full_text.trim()
    ) {
      throw new Error(
        'No readable text was returned by the extraction server.'
      )
    }

    /* RESPECT CURRENT AI ANALYSIS LIMIT */

    if (data.full_text.length > MAX_DOCUMENT_LENGTH) {
      throw new Error(
        'The extracted document exceeds the current 50,000-character AI analysis limit.'
      )
    }

    /* UPDATE UPLOADED DOCUMENT */

    setUploadedText(data.full_text)

    setInputMode('upload')

    setDocumentType('')

    setResult(null)
    setError('')

    /* STORE EXTRACTION METADATA */

    setUploadInfo({
      filename: data.filename || file.name,

      characters:
        data.total_characters ?? data.full_text.length,

      blocks:
        data.total_blocks ??
        (Array.isArray(data.blocks)
          ? data.blocks.length
          : 0),

      warnings:
        Array.isArray(data.warnings)
          ? data.warnings
          : []
    })

  } catch (err) {

    setUploadError(
      err instanceof TypeError
        ? 'Cannot connect to the document extraction server.'
        : err.message || 'Document upload failed.'
    )

  } finally {

    busyRef.current = false
    setUploading(false)

  }
}


  /* ========================================
     ANALYSIS COOLDOWN
     ======================================== */

  useEffect(() => {

    if (cooldown <= 0) return

    const timer = setTimeout(() => {

      setCooldown(seconds => seconds - 1)

    }, 1000)

    return () => clearTimeout(timer)

  }, [cooldown])

  /* ========================================
     AI DOCUMENT ANALYSIS
     ======================================== */

  async function analyzeDocument(event) {
  event.preventDefault()

  if (
    busyRef.current ||
    !documentType ||
    !activeText.trim() ||
    activeText.length > MAX_DOCUMENT_LENGTH ||
    loading ||
    uploading ||
    cooldown > 0
  ) return

  busyRef.current = true

    setCooldown(90)
    setLoading(true)
    setError('')
    setResult(null)

    try {

      const response = await fetch(API_URL, {

        method: 'POST',

        headers: {
          'Content-Type': 'application/json'
        },

body: JSON.stringify({
  text: activeText,
  doc_type: documentType
})

      })

      const data = await response.json().catch(() => null)

      if (!response.ok) {

        const detail = data?.detail

        throw new Error(

          typeof detail === 'string'
            ? detail
            : detail?.message ||
              `Unable to analyze this document (HTTP ${response.status}).`

        )

      }

      if (
        !data ||
        typeof data !== 'object' ||
        Array.isArray(data)
      ) {

        throw new Error(
          'Invalid analysis response from the backend.'
        )

      }

      setResult(data)

      setTimeout(() => {

        document.getElementById('results')?.scrollIntoView({

          behavior: window.matchMedia(
            '(prefers-reduced-motion: reduce)'
          ).matches ? 'instant' : 'smooth',

          block: 'start'

        })

      }, 100)

    } catch (err) {

      setError(

        err instanceof TypeError
          ? 'Could not connect to the backend. Make sure your FastAPI server is running.'
          : err.message || 'Something went wrong. Please try again.'

      )

    } finally {

      busyRef.current = false

      setLoading(false)

    }

  }

  /* ========================================
     PROCESS ANALYSIS RESULTS
     ======================================== */

  const clauses = Array.isArray(result?.clauses)
    ? result.clauses.filter(
        item => item && typeof item === 'object'
      )
    : []

  const keyFacts = Array.isArray(result?.key_facts)
    ? result.key_facts.filter(
        item => item && typeof item === 'object'
      )
    : []

  const missingClauses = Array.isArray(result?.missing_clauses)
    ? result.missing_clauses.filter(
        item =>
          typeof item === 'string' ||
          (item && typeof item === 'object')
      )
    : []

  const riskLevel = String(
    result?.overall_risk?.level || 'unknown'
  ).toLowerCase()

  const riskScore =
    result?.overall_risk?.score == null
      ? NaN
      : Number(result.overall_risk.score)

  const validScore = Number.isFinite(riskScore)
    ? Math.min(100, Math.max(0, riskScore))
    : null

  /* ========================================
     WEBSITE INTERFACE
     ======================================== */

  return (

    <main className="app" ref={appRef}>

      {/* GLOBAL AURORA */}

      <div
        className="aurora site-aurora"
        aria-hidden="true"
      >
        <i />
        <i />
        <i />
      </div>

      {/* =====================================
          HERO AND NAVIGATION
          ===================================== */}

      <div
        className="hero-shell"
        id="home"
        onPointerMove={moveAurora}
        onPointerLeave={resetAurora}
      >

        <div className="aurora" aria-hidden="true">
          <i />
          <i />
          <i />
        </div>

        <header className="navbar">

          <nav
            className="nav-links"
            aria-label="Main navigation"
          >
            <a href="#how-it-works">How it works</a>
            <a href="#features">Features</a>
          </nav>

          <a
            className="brand"
            href="#home"
            aria-label="Lexora AI home"
          >

            <BrandMark />

            <span>Lexora AI</span>

          </a>

          <div className="nav-right">

            <a className="about-link" href="#about">
              About
            </a>

            <MagneticButton
              className="nav-cta"
              onClick={scrollToAnalyzer}
            >
              Get started
              <span aria-hidden="true">↗</span>
            </MagneticButton>

          </div>

        </header>

        <section
          className="hero"
          aria-labelledby="hero-heading"
        >

          <div className="hero-copy">

            <span className="eyebrow">
              <span className="eyebrow-dot" />
              MAKE EVERY WORD COUNT
            </span>

            <h1 className="hero-title" id="hero-heading">

              Understand <span>before you sign.</span>

            </h1>

            <p className="hero-description">

              Complicated agreements, made clear.
              Discover important terms, understand potential
              risks, and know what to ask before you sign.

            </p>

            <div className="hero-actions">

              <MagneticButton
                className="primary-button"
                onClick={scrollToAnalyzer}
              >

                Analyze my document

                <span aria-hidden="true">↗</span>

              </MagneticButton>

              <MagneticButton
                className="secondary-button"
                onClick={loadSample}
                disabled={loading || uploading}
              >

                Try a sample

                <span aria-hidden="true">→</span>

              </MagneticButton>

            </div>

            <span className="hero-note">

              <span className="note-check">✓</span>

              Clarity for the fine print.

            </span>

          </div>

          <ContractPreview
            selected={selectedPreview}
            onSelect={setSelectedPreview}
          />

          <div className="hero-bottom">

            <span>LESS GUESSWORK. MORE CLARITY.</span>

            <a href="#analyzer">
              SCROLL TO EXPLORE ↓
            </a>

          </div>

        </section>

      </div>

      {/* =====================================
          PRODUCT PRINCIPLES
          ===================================== */}

      <section
        className="principles reveal"
        aria-label="Lexora AI principles"
      >

        <div>

          <span className="principle-index">
            01 / UNDERSTAND
          </span>

          <h3>Legal language.</h3>

          <p>
            Complex agreements, explained in plain language.
          </p>

        </div>

        <div>

          <span className="principle-index">
            02 / REVIEW
          </span>

          <h3>Human understanding.</h3>

          <p>
            Review important clauses and potential risks.
          </p>

        </div>

        <div>

          <span className="principle-index">
            03 / DECIDE
          </span>

          <h3>Ask better questions.</h3>

          <p>
            Know what to clarify before you sign.
          </p>

        </div>

      </section>

      {/* =====================================
          ANALYZER SECTION
          ===================================== */}

      <section
        className="analyzer-section"
        id="analyzer"
      >

        <div
          className="section-intro reveal"
          id="how-it-works"
        >

          <span className="eyebrow">

            <span className="eyebrow-dot" />

            YOUR NEXT STEP

          </span>

          <h2>

            Let's decode

            <br />

            <span>the fine print.</span>

          </h2>

          <p>

            Start with your document.
            We'll help make its terms easier to understand.

          </p>

        </div>

        <div className="workspace">

          {/* =================================
              DOCUMENT INPUT
              ================================= */}

          <form
            className="input-card"
            onSubmit={analyzeDocument}
          >

            <div className="card-heading">

              <span className="step-number">01</span>

              <div>

                <h3>Your document</h3>

                <p>
                  Upload a document or paste the text
                  you want to understand.
                </p>

              </div>

            </div>

            <div
  className={`input-mode-switch mode-${inputMode}`}
  role="group"
  aria-label="Document input method"
>
  <span className="mode-indicator" aria-hidden="true" />
  <button
    type="button"
    className={`mode-button ${
      inputMode === 'upload' ? 'active' : ''
    }`}
    aria-pressed={inputMode === 'upload'}
    disabled={loading || uploading}
    onClick={() => changeInputMode('upload')}
  >
    <svg
      viewBox="0 0 24 24"
      width="19"
      height="19"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      aria-hidden="true"
    >
      <path d="M12 16V3M7 8l5-5 5 5" />
      <path d="M4 15v5a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-5" />
    </svg>

    Upload document
  </button>

  <button
    type="button"
    className={`mode-button ${
      inputMode === 'paste' ? 'active' : ''
    }`}
    aria-pressed={inputMode === 'paste'}
    disabled={loading || uploading}
    onClick={() => changeInputMode('paste')}
  >
    <svg
      viewBox="0 0 24 24"
      width="19"
      height="19"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      aria-hidden="true"
    >
      <rect x="5" y="4" width="14" height="17" rx="2" />
      <path d="M9 4V2h6v2M9 10h6M9 14h6M9 18h4" />
    </svg>

    Paste text
  </button>
</div>
           {/* DOCUMENT UPLOAD PANEL */}
{inputMode === 'upload' && (
  <>
    <div
      className={`upload-panel ${
        uploading ? 'is-uploading' : ''
      }`}

              onDragOver={event => event.preventDefault()}

              onDrop={event => {

                event.preventDefault()

                if (busyRef.current) return

                if (event.dataTransfer.files.length !== 1) {

                  setUploadError(
                    'Please drop one document at a time.'
                  )

                  return

                }

                uploadDocument(event.dataTransfer.files[0])

              }}

              aria-busy={uploading}
            >

              <div className="upload-icon">

                <svg
                  viewBox="0 0 24 24"
                  width="30"
                  height="30"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden="true"
                >

                  <path d="M7 17H5a4 4 0 0 1-.7-7.9A8 8 0 0 1 19 9a4 4 0 0 1 0 8h-2" />

                  <path d="M12 21V11M8 15l4-4 4 4" />

                </svg>

              </div>

              <h3>Upload your contract.</h3>

              <p>
                Drag and drop a document or browse your files.
              </p>

              <input
                type="file"
                ref={fileInputRef}
                accept=".pdf,.docx,.txt"
                hidden
                disabled={uploading || loading}

                onChange={event => {

                  const file = event.target.files?.[0]

                  event.target.value = ''

                  uploadDocument(file)

                }}
              />

              <MagneticButton
                className="primary-button"
                disabled={uploading || loading}
                onClick={() => fileInputRef.current?.click()}
              >

                {uploading
                  ? 'Extracting document...'
                  : 'Choose file ↗'}

              </MagneticButton>

              <span className="upload-formats">

                PDF · DOCX · TXT — Up to 25 MB

              </span>

              <p className="upload-privacy">

                Files are sent to our backend.
                Avoid uploading confidential documents.

              </p>

            </div>

            {/* UPLOAD SUCCESS */}

            {uploadInfo && (

              <div
                className="upload-success"
                role="status"
              >

                <strong>✓ {uploadInfo.filename}</strong>

                <p>

                  {uploadInfo.characters.toLocaleString()}
                  {' '}characters extracted

                  {' '}· {uploadInfo.blocks} source blocks

                </p>

                {uploadInfo.warnings.map((warning, index) => (

                  <p
                    key={index}
                    className="upload-warning"
                  >

                    {warning}

                  </p>

                ))}

              </div>

            )}

            {/* UPLOAD ERROR */}

            {uploadError && (

              <div
                className="error-box upload-error"
                role="alert"
              >

                {uploadError}

              </div>

            )}

                <p className="analysis-limit-note">
      Analysis currently supports up to 50,000
      extracted characters per document.
    </p>

    {uploadInfo && (
      <details className="extracted-preview">
        <summary>Preview extracted text</summary>
        <pre>{uploadedText}</pre>
      </details>
    )}
  </>
)}

{/* DOCUMENT TYPE TOOLBAR */}


            <div className="form-toolbar">

              <label htmlFor="documentType">

                DOCUMENT TYPE

              </label>

              <button
                type="button"
                className="sample-link"
                onClick={loadSample}
                disabled={loading || uploading}
              >

                Load fictional sample ↗

              </button>

            </div>

            {/* DOCUMENT TYPE SELECTOR */}

            <select
              id="documentType"
              value={documentType}

              onChange={event => {

                setDocumentType(event.target.value)

                setError('')
                setResult(null)

              }}

              required
              disabled={loading || uploading}
            >

              <option value="" disabled>

                Select a document type first

              </option>

              <optgroup label="Property & Housing">

                <option value="rental_agreement">
                  Rental / lease agreement
                </option>

                <option value="property_sale_agreement">
                  Property sale agreement
                </option>

                <option value="commercial_lease">
                  Commercial lease
                </option>

                <option value="property_management_agreement">
                  Property management agreement
                </option>

              </optgroup>

              <optgroup label="Employment & Careers">

                <option value="employment_contract">
                  Employment contract
                </option>

                <option value="offer_letter">
                  Job offer letter
                </option>

                <option value="freelance_agreement">
                  Freelance / independent contractor agreement
                </option>

                <option value="internship_agreement">
                  Internship agreement
                </option>

                <option value="nda">
                  Non-disclosure agreement (NDA)
                </option>

                <option value="non_compete_agreement">
                  Non-compete agreement
                </option>

              </optgroup>

              <optgroup label="Sports & Entertainment">

                <option value="football_player_contract">
                  Football player contract
                </option>

                <option value="athlete_agreement">
                  Professional athlete agreement
                </option>

                <option value="sports_sponsorship_agreement">
                  Sports sponsorship agreement
                </option>

                <option value="image_rights_agreement">
                  Image rights / endorsement agreement
                </option>

                <option value="talent_agreement">
                  Talent / artist agreement
                </option>

              </optgroup>

              <optgroup label="Business & Commercial">

                <option value="service_agreement">
                  Service agreement
                </option>

                <option value="business_partnership_agreement">
                  Business partnership agreement
                </option>

                <option value="shareholders_agreement">
                  Shareholders' agreement
                </option>

                <option value="vendor_supplier_agreement">
                  Vendor / supplier agreement
                </option>

                <option value="consulting_agreement">
                  Consulting agreement
                </option>

                <option value="franchise_agreement">
                  Franchise agreement
                </option>

              </optgroup>

              <optgroup label="Finance & Payments">

                <option value="loan_agreement">
                  Loan agreement
                </option>

                <option value="investment_agreement">
                  Investment agreement
                </option>

                <option value="payment_agreement">
                  Payment / installment agreement
                </option>

                <option value="personal_guarantee">
                  Personal guarantee
                </option>

                <option value="debt_settlement_agreement">
                  Debt settlement agreement
                </option>

              </optgroup>

              <optgroup label="Technology & Digital">

                <option value="software_development_agreement">
                  Software development agreement
                </option>

                <option value="saas_subscription_agreement">
                  Software / SaaS subscription agreement
                </option>

                <option value="website_development_contract">
                  Website development contract
                </option>

                <option value="software_license_agreement">
                  Software licence agreement
                </option>

                <option value="data_processing_agreement">
                  Data processing agreement
                </option>

              </optgroup>

              <optgroup label="Sales & Services">

                <option value="sales_agreement">
                  Sales agreement
                </option>

                <option value="purchase_agreement">
                  Purchase agreement
                </option>

                <option value="distribution_agreement">
                  Distribution agreement
                </option>

                <option value="marketing_agreement">
                  Marketing agreement
                </option>

                <option value="maintenance_agreement">
                  Maintenance agreement
                </option>

              </optgroup>

              <optgroup label="General & Other">

                <option value="insurance_policy">
                  Insurance policy
                </option>

                <option value="copyright_license_agreement">
                  Copyright / IP licence agreement
                </option>

                <option value="memorandum_of_understanding">
                  Memorandum of understanding (MoU)
                </option>

                <option value="government_service_contract">
                  Government / public service contract
                </option>

                <option value="other">
                  Other / unsure
                </option>

              </optgroup>

            </select>


{/* DOCUMENT TEXT AREA */}

{inputMode === 'paste' && (
  <>
    <label htmlFor="documentText">
      DOCUMENT TEXT
    </label>

    <textarea
      id="documentText"
      value={documentText}
      onChange={event => {
        setDocumentText(event.target.value)
        setResult(null)
        setError('')
      }}
      placeholder={
        documentType
          ? 'Paste the text of your selected document here...'
          : 'Select a document type above to unlock this field.'
      }
      rows={9}
      maxLength={MAX_DOCUMENT_LENGTH}
      disabled={!documentType || loading || uploading}
      required
    />

    <div className="input-meta">
      <span>
        {documentText.length.toLocaleString()}
        {' / '}
        {MAX_DOCUMENT_LENGTH.toLocaleString()} characters
      </span>

      <span>
        Remove personal details before analysis.
      </span>
    </div>
  </>
)}


            {/* SINGLE CORRECT SUBMIT BUTTON */}


<MagneticButton
  type="submit"
  className="primary-button submit-button"
  disabled={
    !documentType ||
    loading ||
    uploading ||
    cooldown > 0 ||
    !activeText.trim() ||
    activeText.length > MAX_DOCUMENT_LENGTH
  }
  aria-busy={loading || uploading}
>
  {uploading ? (
    'Extracting document...'
  ) : loading ? (
    <>
      <span
        className="button-spinner"
        aria-hidden="true"
      />
      Analyzing document...
    </>
  ) : cooldown > 0 ? (
    `Try again in ${cooldown}s`
  ) : (
    <>
      Decode my document
      <span aria-hidden="true">↗</span>
    </>
  )}
</MagneticButton>


            <p className="privacy-note">

              Your text is sent to our configured backend for analysis.
              Avoid including sensitive personal information.

            </p>

          </form>

          {/* =================================
              ANALYSIS RESULTS
              ================================= */}

          <section
            className="results-card"
            id="results"
            aria-live="polite"
          >

            <div className="card-heading">

              <span className="step-number">02</span>

              <div>

                <h3>Your insights</h3>

                <p>
                  A clearer picture of what matters.
                </p>

              </div>

            </div>

            {/* EMPTY RESULTS STATE */}

            {!result && !error && !loading && (

              <div className="empty-state">

                <div className="empty-symbol">✳</div>

                <h3>Clarity is on its way.</h3>

                <p>

                  Your summary, key facts, and clauses to review
                  will appear here after analysis.

                </p>

                <div className="empty-lines">
                  <span />
                  <span />
                  <span />
                </div>

              </div>

            )}

            {/* =================================
                DOCUMENT INTELLIGENCE LOADER
                ================================= */}

            {loading && (

              <div
                className="loading-state"
                role="status"
              >

                <div
                  className="decoder-visual"
                  aria-hidden="true"
                >

                  <div className="decoder-halo" />

                  <div className="decoder-paper">

                    <div className="decoder-fold" />

                    <div className="decoder-paper-heading" />

                    <div className="decoder-line" />

                    <div className="decoder-line short" />

                    <div className="decoder-line highlighted" />

                    <div className="decoder-line" />

                    <div className="decoder-line short" />

                    <div className="decoder-scan" />

                  </div>

                  <div className="decoder-bubble bubble-left">

                    ✳

                  </div>

                  <div className="decoder-bubble bubble-right">

                    <svg
                      viewBox="0 0 24 24"
                      width="22"
                      height="22"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.8"
                    >

                      <circle cx="10" cy="10" r="6" />

                      <path
                        d="m15 15 5 5"
                        strokeLinecap="round"
                      />

                    </svg>

                  </div>

                </div>

                <h3>Decoding your document.</h3>

                <p>

                  Making complex terms easier to understand.
                  Our AI is reviewing your agreement.

                </p>

                <div className="decoder-status">

                  <span
                    className="decoder-dots"
                    aria-hidden="true"
                  >
                    <i />
                    <i />
                    <i />
                  </span>

                  Analysis in progress

                </div>

              </div>

            )}

            {/* ANALYSIS ERROR */}

            {error && (

              <div
                className="error-box"
                role="alert"
              >

                {error}

              </div>

            )}

            {/* =================================
                SUCCESSFUL ANALYSIS RESULTS
                ================================= */}

            {result && (

              <div className="analysis-result">

                {/* OVERALL RISK */}

                {result.overall_risk && (

                  <div
                    className={`risk-overview risk-${riskLevel}`}
                  >

                    <div className="risk-overview-copy">

                      <span className="result-label">

                        OVERALL RISK ASSESSMENT

                      </span>

                      <h3>

                        {riskLevel === 'unknown'
                          ? 'Not rated'
                          : `${riskLevel} risk`}

                      </h3>

                      <p className="risk-description">

                        A preliminary screening indicator based on
                        the analyzed provisions, not a legal verdict.

                      </p>

                    </div>

                    {validScore !== null && (

                      <div
                        className="risk-score"
                        role="img"
                        aria-label={`Risk score: ${validScore} out of 100`}
                      >

                        <AnimatedScore
                          key={validScore}
                          value={validScore}
                        />

                        <span>/100</span>

                      </div>

                    )}

                    {validScore !== null && (

                      <div
                        className="risk-meter"
                        role="meter"
                        aria-label="Overall risk score"
                        aria-valuemin={0}
                        aria-valuemax={100}
                        aria-valuenow={validScore}
                      >

                        <div
                          className="risk-meter-fill"
                          style={{
                            width: `${validScore}%`
                          }}
                        />

                      </div>

                    )}

                  </div>

                )}

                {/* EXECUTIVE SUMMARY */}

                <h4>Executive summary</h4>

                <p>

                  {result.summary || 'No summary provided.'}

                </p>

                {/* KEY FACTS */}

                <h4>Key facts</h4>

                {keyFacts.length > 0 ? (

                  <div className="key-facts-grid">

                    {keyFacts.map((fact, index) => (

                      <div
                        className="key-fact-card"
                        key={`${fact.label}-${index}`}
                      >

                        <span className="key-fact-label">

                          {fact.label || `Fact ${index + 1}`}

                        </span>

                        <span className="key-fact-value">

                          {fact.value ?? 'Not specified'}

                        </span>

                      </div>

                    ))}

                  </div>

                ) : (

                  <p>No key facts were returned.</p>

                )}

                {/* IMPORTANT CLAUSE FINDINGS */}

                <h4>Clauses to review</h4>

                <p className="results-hint">

                  Important findings are shown first.
                  Select a finding to view its original wording,
                  explanation, and suggested questions.

                </p>

                {clauses.length > 0 ? (

                  <div className="findings-list">

                    {clauses.map((clause, index) => {

                      const rawRisk = String(
                        clause.risk || 'yellow'
                      ).toLowerCase()

                      const risk = ['red', 'yellow', 'green'].includes(rawRisk)
                        ? rawRisk
                        : 'yellow'

                      const badgeLabel =
                        risk === 'red'
                          ? 'HIGH RISK'
                          : risk === 'yellow'
                            ? 'REVIEW'
                            : 'LOW RISK'

                      return (

                        <details
                          className={`result-clause result-clause-${risk}`}
                          key={clause.id ?? index}
                        >

                          <summary className="finding-summary">

                            <span
                              className={`risk-badge risk-badge-${risk}`}
                            >

                              {badgeLabel}

                            </span>

                            <span className="finding-title">

                              {clause.category ||
                                'Contract provision'}

                            </span>

                            <span
                              className="finding-toggle"
                              aria-hidden="true"
                            >

                              +

                            </span>

                          </summary>

                          <div className="finding-details">

                            {/* EXPLANATION */}

                            {clause.explanation && (

                              <p className="finding-explanation">

                                {clause.explanation}

                              </p>

                            )}

                            {/* ORIGINAL WORDING */}

                            {clause.text && (

                              <div className="evidence-block">

                                <span className="evidence-label">

                                  ORIGINAL WORDING

                                </span>

                                <blockquote className="clause-quote">

                                  {clause.text}

                                </blockquote>

                              </div>

                            )}

                            {/* WHY IT MATTERS */}

                            {clause.why_risky && (

                              <div className="evidence-block">

                                <span className="evidence-label">

                                  WHY IT MATTERS

                                </span>

                                <p>{clause.why_risky}</p>

                              </div>

                            )}

                            {/* SUGGESTED QUESTIONS */}

                            {Array.isArray(clause.questions) &&
                              clause.questions.length > 0 && (

                              <div className="evidence-block">

                                <span className="evidence-label">

                                  QUESTIONS TO ASK

                                </span>

                                <ul>

                                  {clause.questions.map(
                                    (question, questionIndex) => (

                                      <li key={questionIndex}>

                                        {question}

                                      </li>

                                    )
                                  )}

                                </ul>

                              </div>

                            )}

                          </div>

                        </details>

                      )

                    })}

                  </div>

                ) : (

                  <div className="no-findings">

                    <strong>

                      No significant findings were returned.

                    </strong>

                    <p>

                      This does not guarantee that the contract
                      is safe or complete.
                      Review the original terms carefully.

                    </p>

                  </div>

                )}

                {/* MISSING PROTECTIONS */}

                {missingClauses.length > 0 && (

                  <>

                    <h4>Protections to check</h4>

                    <div className="missing-clauses-list">

                      {missingClauses.map((item, index) => (

                        <details
                          className="missing-clause"
                          key={index}
                        >

                          <summary>

                            {typeof item === 'string'
                              ? item
                              : item.clause_name ||
                                item.name ||
                                'Protection to check'}

                          </summary>

                          {typeof item !== 'string' && (

                            <p>

                              {item.reason ||
                                item.description ||
                                'Check whether this protection is addressed elsewhere in the agreement.'}

                            </p>

                          )}

                        </details>

                      ))}

                    </div>

                  </>

                )}

                {/* LEGAL DISCLAIMER */}

                <p className="disclaimer">

                  {result.disclaimer ||
                    'This is general information, not legal advice.'}

                </p>

              </div>

            )}

          </section>

        </div>

      </section>

      {/* =====================================
          CLOSING SECTION
          ===================================== */}

      <section
        className="closing-section reveal"
        id="features"
      >

        <span className="eyebrow">

          A LITTLE MORE CLARITY GOES A LONG WAY

        </span>

        <h2>

          Understand the words.

          <br />

          <span>Ask better questions.</span>

        </h2>

        <MagneticButton
          className="primary-button"
          onClick={scrollToAnalyzer}
        >

          Start decoding ↗

        </MagneticButton>

      </section>

      {/* =====================================
          FOOTER
          ===================================== */}

      <footer className="footer" id="about">

        <a
          className="brand"
          href="#home"
          aria-label="Lexora AI home"
        >

          <BrandMark />

          <span>Lexora AI</span>

        </a>

        <div className="footer-credits">

          <span>CREATED BY</span>

          <strong>Sabari Ranganathan</strong>

          <span className="footer-version">

            Version 1.1 · Aurora Update

          </span>

        </div>

        <span className="footer-disclaimer">

          General information only.
          Not a substitute for legal advice.

        </span>

        <span>

          © 2026 Lexora AI. All rights reserved.

        </span>

      </footer>

    </main>

  )

}

export default App
