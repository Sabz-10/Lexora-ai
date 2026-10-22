
import { useEffect, useState } from 'react'
import './App.css'

function App() {
  const MAX_DOCUMENT_LENGTH = 50000

  const [documentText, setDocumentText] = useState('')
  const [documentType, setDocumentType] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [cooldown, setCooldown] = useState(0)

  useEffect(() => {
    if (cooldown <= 0) return

    const timer = setTimeout(() => {
      setCooldown((seconds) => seconds - 1)
    }, 1000)

    return () => clearTimeout(timer)
  }, [cooldown])

  async function analyzeDocument(event) {
    event.preventDefault()

    if (!documentType || !documentText.trim() || loading || cooldown > 0) return

    setCooldown(90)
    setLoading(true)
    setError('')
    setResult(null)

    try {

const response = await fetch(
  import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/analyze',
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      text: documentText,
      doc_type: documentType,
    }),
  }
)


      const data = await response.json()

      if (!response.ok) {
        const detail = data.detail
        throw new Error(
          typeof detail === 'string'
            ? detail
            : detail?.message || 'Unable to analyze this document.'
        )
      }

      setResult(data)

      setTimeout(() => {
        document.getElementById('results')?.scrollIntoView({
          behavior: 'smooth',
          block: 'start',
        })
      }, 100)
    } catch (err) {
      setError(
        err instanceof TypeError
          ? 'Could not connect to the backend. Make sure your FastAPI server is running.'
          : err.message || 'Something went wrong. Please try again.'
      )
    } finally {
      setLoading(false)
    }
  }

  function scrollToAnalyzer() {
    document.getElementById('analyzer')?.scrollIntoView({
      behavior: 'smooth',
    })
  }

  const clauses = result?.clauses || []
  const keyFacts = result?.key_facts || []
  const missingClauses = result?.missing_clauses || []
  const riskLevel = String(result?.overall_risk?.level || 'unknown').toLowerCase()
  const riskScore = Number(result?.overall_risk?.score)
  const validScore = Number.isFinite(riskScore)
    ? Math.min(100, Math.max(0, riskScore))
    : null

  return (
    <main className="app">
      {/* NAVBAR */}
      <header className="navbar">
        <a className="brand" href="#home" aria-label="Lexora AI home">
          <span className="brand-mark">
            <svg viewBox="0 0 32 32" fill="none" aria-hidden="true">
              <path d="M9 4.5h10l5 5V27H9V4.5Z" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
              <path d="M19 4.5v6h5M13 16h7M13 20h7M13 24h4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
          </span>
          <span>Lexora AI</span>
        </a>

        <span className="brand-tagline">Clarity for the fine print.</span>

        <nav className="nav-links" aria-label="Main navigation">
          <a href="#how-it-works">How it works</a>
          <a href="#features">Features</a>
          <a href="#about">About</a>
        </nav>

        <button className="nav-cta" onClick={scrollToAnalyzer}>
          Get started <span aria-hidden="true">↗</span>
        </button>
      </header>

      {/* HERO */}
      <section className="hero" id="home">
        <div className="hero-copy">
          <div className="eyebrow">
            <span className="eyebrow-dot" />
            MAKE EVERY WORD COUNT
          </div>

          <h1 className="hero-title">
            Legal language.
            <br />
            <span>Human</span>
            <br />
            understanding.
          </h1>

          <p className="hero-description">
            Complicated agreements, made clear. Discover important terms,
            understand potential risks, and know what to ask before you sign.
          </p>

          <div className="hero-actions">
            <button className="primary-button" onClick={scrollToAnalyzer}>
              Analyze my document <span aria-hidden="true">↗</span>
            </button>
            <span className="hero-note">
              <span className="note-check">✓</span>
              Clearer decisions start here
            </span>
          </div>

          <div className="social-row">
            <span className="connect-label">BUILT FOR CLARITY</span>
            <span className="connect-line" />
            <span className="social-chip">01 / Understand</span>
            <span className="social-chip">02 / Review</span>
            <span className="social-chip">03 / Decide</span>
          </div>
        </div>

        <div className="hero-art" aria-label="Illustration of a contract review">
          <div className="art-orbit orbit-one" />
          <div className="art-orbit orbit-two" />

          <div className="floating-label label-top">
            <span className="label-symbol">✳</span>
            Clarity, at a glance
          </div>

          <div className="document-card">
            <div className="document-topline">
              <span className="document-icon">▤</span>
              <span className="document-status">DOCUMENT PREVIEW</span>
              <span className="document-menu">•••</span>
            </div>

            <div className="document-title">
              <span className="tiny-label">AGREEMENT / 001</span>
              <h2>Rental Agreement</h2>
              <p>Key terms worth understanding.</p>
            </div>

            <div className="document-divider" />

            <div className="preview-clause">
              <div className="clause-number">01</div>
              <div className="clause-content">
                <strong>Security deposit</strong>
                <span>Refund terms and deductions</span>
              </div>
              <span className="preview-tag tag-review">REVIEW</span>
            </div>

            <div className="preview-clause">
              <div className="clause-number">02</div>
              <div className="clause-content">
                <strong>Termination</strong>
                <span>Notice period and conditions</span>
              </div>
              <span className="preview-tag tag-check">CHECK</span>
            </div>

            <div className="preview-clause">
              <div className="clause-number">03</div>
              <div className="clause-content">
                <strong>Monthly rent</strong>
                <span>Payment date and amount</span>
              </div>
              <span className="preview-tag tag-clear">CLEAR</span>
            </div>

            <div className="document-footer">
              <span className="footer-sparkle">✳</span>
              <span>Your document, decoded.</span>
              <span className="footer-arrow">↗</span>
            </div>
          </div>

          <div className="floating-label label-bottom">
            <span className="label-pulse" />
            From complex to clear.
          </div>

          <div className="art-star star-one">✳</div>
          <div className="art-star star-two">✳</div>
        </div>

        <div className="hero-bottom">
          <span>LESS GUESSWORK. MORE CLARITY.</span>
          <span>SCROLL TO EXPLORE ↓</span>
        </div>

        <div className="wave-art" aria-hidden="true">
          <svg viewBox="0 0 1440 330" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="waveBase" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="#f5a4c7" />
                <stop offset="30%" stopColor="#ff875e" />
                <stop offset="58%" stopColor="#ffcc67" />
                <stop offset="78%" stopColor="#d99bea" />
                <stop offset="100%" stopColor="#7044b8" />
              </linearGradient>
              <linearGradient id="wavePink" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="#f05ca8" />
                <stop offset="48%" stopColor="#ff9c80" />
                <stop offset="100%" stopColor="#ffcf78" />
              </linearGradient>
              <linearGradient id="wavePurple" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="#e2a4f1" />
                <stop offset="52%" stopColor="#a06bdb" />
                <stop offset="100%" stopColor="#5935a3" />
              </linearGradient>
            </defs>
            <path d="M0 120 C190 35 285 200 475 145 S745 12 920 110 S1210 185 1440 42 L1440 330 L0 330Z" fill="url(#waveBase)" />
            <path d="M0 182 C170 90 300 230 475 178 S750 65 920 150 S1200 220 1440 105 L1440 330 L0 330Z" fill="url(#wavePink)" opacity=".95" />
            <path d="M0 238 C205 130 310 278 520 210 S790 105 985 192 S1250 260 1440 155 L1440 330 L0 330Z" fill="url(#wavePurple)" opacity=".92" />
            <path d="M0 286 C190 210 365 310 575 255 S880 178 1080 250 S1310 285 1440 230 L1440 330 L0 330Z" fill="#50318c" opacity=".6" />
          </svg>
        </div>
      </section>

      {/* ANALYZER */}
      <section className="analyzer-section" id="analyzer">
        <div className="section-intro" id="how-it-works">
          <span className="eyebrow">
            <span className="eyebrow-dot" />
            YOUR NEXT STEP
          </span>
          <h2>
            Let's decode
            <br />
            <span>the fine print.</span>
          </h2>
          <p>Start with your document. We'll help make its terms easier to understand.</p>
        </div>

        <div className="workspace">
          {/* INPUT */}
          <form className="input-card" onSubmit={analyzeDocument}>
            <div className="card-heading">
              <span className="step-number">01</span>
              <div>
                <h3>Your document</h3>
                <p>Paste the text you want to understand.</p>
              </div>
            </div>

            <label htmlFor="documentType">DOCUMENT TYPE</label>
            <select
              id="documentType"
              value={documentType}
              onChange={(event) => {
                setDocumentType(event.target.value)
                setError('')
                setResult(null)
              }}
              required
            >
              <option value="" disabled>Select a document type first</option>

              <optgroup label="Property & Housing">
                <option value="rental_agreement">Rental / lease agreement</option>
                <option value="property_sale_agreement">Property sale agreement</option>
                <option value="commercial_lease">Commercial lease</option>
                <option value="property_management_agreement">Property management agreement</option>
              </optgroup>

              <optgroup label="Employment & Careers">
                <option value="employment_contract">Employment contract</option>
                <option value="offer_letter">Job offer letter</option>
                <option value="freelance_agreement">Freelance / independent contractor agreement</option>
                <option value="internship_agreement">Internship agreement</option>
                <option value="nda">Non-disclosure agreement (NDA)</option>
                <option value="non_compete_agreement">Non-compete agreement</option>
              </optgroup>

              <optgroup label="Sports & Entertainment">
                <option value="football_player_contract">Football player contract</option>
                <option value="athlete_agreement">Professional athlete agreement</option>
                <option value="sports_sponsorship_agreement">Sports sponsorship agreement</option>
                <option value="image_rights_agreement">Image rights / endorsement agreement</option>
                <option value="talent_agreement">Talent / artist agreement</option>
              </optgroup>

              <optgroup label="Business & Commercial">
                <option value="service_agreement">Service agreement</option>
                <option value="business_partnership_agreement">Business partnership agreement</option>
                <option value="shareholders_agreement">Shareholders' agreement</option>
                <option value="vendor_supplier_agreement">Vendor / supplier agreement</option>
                <option value="consulting_agreement">Consulting agreement</option>
                <option value="franchise_agreement">Franchise agreement</option>
              </optgroup>

              <optgroup label="Finance & Payments">
                <option value="loan_agreement">Loan agreement</option>
                <option value="investment_agreement">Investment agreement</option>
                <option value="payment_agreement">Payment / installment agreement</option>
                <option value="personal_guarantee">Personal guarantee</option>
                <option value="debt_settlement_agreement">Debt settlement agreement</option>
              </optgroup>

              <optgroup label="Technology & Digital">
                <option value="software_development_agreement">Software development agreement</option>
                <option value="saas_subscription_agreement">Software / SaaS subscription agreement</option>
                <option value="website_development_contract">Website development contract</option>
                <option value="software_license_agreement">Software licence agreement</option>
                <option value="data_processing_agreement">Data processing agreement</option>
              </optgroup>

              <optgroup label="Sales & Services">
                <option value="sales_agreement">Sales agreement</option>
                <option value="purchase_agreement">Purchase agreement</option>
                <option value="distribution_agreement">Distribution agreement</option>
                <option value="marketing_agreement">Marketing agreement</option>
                <option value="maintenance_agreement">Maintenance agreement</option>
              </optgroup>

              <optgroup label="General & Other">
                <option value="insurance_policy">Insurance policy</option>
                <option value="copyright_license_agreement">Copyright / IP licence agreement</option>
                <option value="memorandum_of_understanding">Memorandum of understanding (MoU)</option>
                <option value="government_service_contract">Government / public service contract</option>
                <option value="other">Other / unsure</option>
              </optgroup>
            </select>

            <label htmlFor="documentText">DOCUMENT TEXT</label>
            <textarea
              id="documentText"
              value={documentText}
              onChange={(event) => setDocumentText(event.target.value)}
              placeholder={
                documentType
                  ? "Paste the text of your selected document type here..."
                  : "Select a document type above to unlock this field."
              }
              rows={9}
              maxLength={MAX_DOCUMENT_LENGTH}
              disabled={!documentType}
              required
            />

            <div className="input-meta">
              <span>
                {documentText.length.toLocaleString()} / 50,000 characters
              </span>
              <span>Remove personal details before pasting.</span>
            </div>

            <button
              type="submit"
              className="primary-button submit-button"
              disabled={!documentType || loading || cooldown > 0 || !documentText.trim()}
              aria-busy={loading}
            >
              {loading ? (
                <>
                  <span className="button-spinner" aria-hidden="true" />
                  Analyzing document...
                </>
              ) : cooldown > 0 ? (
                `Try again in ${cooldown}s`
              ) : (
                <>
                  Decode my document <span aria-hidden="true">↗</span>
                </>
              )}
            </button>

            <p className="privacy-note">
              Your text is sent to our configured backend for analysis.
              Avoid including sensitive personal information.
            </p>
          </form>

          {/* RESULTS */}
          <section className="results-card" id="results" aria-live="polite">
            <div className="card-heading">
              <span className="step-number">02</span>
              <div>
                <h3>Your insights</h3>
                <p>A clearer picture of what matters.</p>
              </div>
            </div>

            {!result && !error && !loading && (
              <div className="empty-state">
                <div className="empty-symbol">✳</div>
                <h3>Clarity is on its way.</h3>
                <p>
                  Your summary, key facts, and clauses to review will appear
                  here after analysis.
                </p>
                <div className="empty-lines">
                  <span />
                  <span />
                  <span />
                </div>
              </div>
            )}

            {loading && (
              <div className="loading-state" role="status">
                <span className="loading-spinner" aria-hidden="true" />
                <h3>Decoding your document...</h3>
                <p>
                  Our AI is reviewing the terms and identifying clauses that
                  may deserve a closer look.
                </p>
                <span className="loading-caption">This may take a few moments.</span>
              </div>
            )}

            {error && <div className="error-box" role="alert">{error}</div>}

            {result && (
              <div className="analysis-result">
                {/* OVERALL RISK */}
                {result.overall_risk && (
                  <div className={`risk-overview risk-${riskLevel}`}>
                    <div className="risk-overview-copy">
                      <span className="result-label">OVERALL RISK ASSESSMENT</span>
                      <h3>{riskLevel === 'unknown' ? 'Not rated' : `${riskLevel} risk`}</h3>
                      <p className="risk-description">
                        A preliminary screening indicator based on the analyzed
                        provisions, not a legal verdict.
                      </p>
                    </div>

                    {validScore !== null && (
                      <div
                        className="risk-score"
                        role="img"
                        aria-label={`Risk score: ${validScore} out of 100`}
                      >
                        <strong>{validScore}</strong>
                        <span>/100</span>
                      </div>
                    )}

                    {validScore !== null && (
                      <div
                        className="risk-meter"
                        role="progressbar"
                        aria-label="Overall risk score"
                        aria-valuemin={0}
                        aria-valuemax={100}
                        aria-valuenow={validScore}
                      >
                        <div
                          className="risk-meter-fill"
                          style={{ width: `${validScore}%` }}
                        />
                      </div>
                    )}
                  </div>
                )}

                {/* SUMMARY */}
                <h4>Executive summary</h4>
                <p>{result.summary || 'No summary provided.'}</p>

                {/* KEY FACTS */}
                <h4>Key facts</h4>
                {keyFacts.length ? (
                  <div className="key-facts-grid">
                    {keyFacts.map((fact, index) => (
                      <div className="key-fact-card" key={`${fact.label}-${index}`}>
                        <span className="key-fact-label">
                          {fact.label || `Fact ${index + 1}`}
                        </span>
                        <span className="key-fact-value">
                          {fact.value || 'Not specified'}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p>No key facts were returned.</p>
                )}

                {/* IMPORTANT FINDINGS */}
                <h4>Clauses to review</h4>
                <p className="results-hint">
                  Important findings are shown first. Select a finding to view
                  its original wording, explanation, and suggested questions.
                </p>

                {clauses.length ? (
                  <div className="findings-list">
                    {clauses.map((clause, index) => {
                      const risk = String(clause.risk || 'yellow').toLowerCase()
                      const badgeLabel =
                        risk === 'red' ? 'HIGH RISK' :
                        risk === 'yellow' ? 'REVIEW' : 'LOW RISK'

                      return (
                        <details
                          className={`result-clause result-clause-${risk}`}
                          key={clause.id ?? index}
                        >
                          <summary className="finding-summary">
                            <span className={`risk-badge risk-badge-${risk}`}>
                              {badgeLabel}
                            </span>
                            <span className="finding-title">
                              {clause.category || 'Contract provision'}
                            </span>
                            <span className="finding-toggle" aria-hidden="true">+</span>
                          </summary>

                          <div className="finding-details">
                            {clause.explanation && (
                              <p className="finding-explanation">
                                {clause.explanation}
                              </p>
                            )}

                            {clause.text && (
                              <div className="evidence-block">
                                <span className="evidence-label">ORIGINAL WORDING</span>
                                <blockquote className="clause-quote">
                                  {clause.text}
                                </blockquote>
                              </div>
                            )}

                            {clause.why_risky && (
                              <div className="evidence-block">
                                <span className="evidence-label">WHY IT MATTERS</span>
                                <p>{clause.why_risky}</p>
                              </div>
                            )}

                            {clause.questions?.length > 0 && (
                              <div className="evidence-block">
                                <span className="evidence-label">QUESTIONS TO ASK</span>
                                <ul>
                                  {clause.questions.map((question, questionIndex) => (
                                    <li key={questionIndex}>{question}</li>
                                  ))}
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
                    <strong>No significant findings were returned.</strong>
                    <p>
                      This does not guarantee that the contract is safe or
                      complete. Review the original terms carefully.
                    </p>
                  </div>
                )}

                {/* MISSING PROTECTIONS */}
                {missingClauses.length > 0 && (
                  <>
                    <h4>Protections to check</h4>
                    <div className="missing-clauses-list">
                      {missingClauses.map((item, index) => (
                        <details className="missing-clause" key={index}>
                          <summary>
                            {typeof item === 'string'
                              ? item
                              : item.clause_name || item.name || 'Protection to check'}
                          </summary>
                          {typeof item !== 'string' && (
                            <p>
                              {item.reason || item.description ||
                                'Check whether this protection is addressed elsewhere in the agreement.'}
                            </p>
                          )}
                        </details>
                      ))}
                    </div>
                  </>
                )}

                <p className="disclaimer">
                  {result.disclaimer || 'This is general information, not legal advice.'}
                </p>
              </div>
            )}
          </section>
        </div>
      </section>

      {/* CLOSING SECTION */}
      <section className="closing-section" id="features">
        <span className="eyebrow">A LITTLE MORE CLARITY GOES A LONG WAY</span>
        <h2>
          Understand the words.
          <br />
          <span>Ask better questions.</span>
        </h2>
        <button className="primary-button" onClick={scrollToAnalyzer}>
          Start decoding ↗
        </button>
      </section>

      {/* FOOTER */}
      <footer className="footer" id="about">
        <a className="brand" href="#home" aria-label="Lexora AI home">
          <span className="brand-mark">
            <svg viewBox="0 0 32 32" fill="none" aria-hidden="true">
              <path d="M9 4.5h10l5 5V27H9V4.5Z" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
              <path d="M19 4.5v6h5M13 16h7M13 20h7M13 24h4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
          </span>
          <span>Lexora AI</span>
        </a>

        <div className="footer-credits">
          <span>CREATED BY</span>
          <strong>Sabari Ranganathan</strong>
          <span className="footer-version">Version 1.0 · MVP</span>
        </div>

        <span className="footer-disclaimer">
          General information only. Not a substitute for legal advice.
        </span>
        <span>© 2026 Lexora AI. All rights reserved.</span>
      </footer>
    </main>
  )
}

export default App
