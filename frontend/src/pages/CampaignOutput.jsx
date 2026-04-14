import { useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'

// ─── Helpers ────────────────────────────────────────────────────────────────

function copyToClipboard(text) {
  navigator.clipboard.writeText(text).catch(() => {})
}

function slugify(text) {
  return text.toLowerCase().replace(/[^\w\s-]/g, '').replace(/[\s_-]+/g, '_').slice(0, 40)
}

// ─── Sub-components ─────────────────────────────────────────────────────────

function StatusBar({ status }) {
  const cfg = {
    pending:  { color: 'text-gray-400', dot: 'bg-gray-600',    label: 'Pending' },
    running:  { color: 'text-orange-400', dot: 'bg-[#FF4500] pulse-orange', label: 'Running pipeline…' },
    complete: { color: 'text-green-400', dot: 'bg-green-500',  label: 'Complete' },
    failed:   { color: 'text-red-400',   dot: 'bg-red-500',    label: 'Failed' },
  }[status] || { color: 'text-gray-400', dot: 'bg-gray-600', label: status }

  return (
    <div className="flex items-center gap-3 px-6 py-4 border-b border-[#2a2a2a] bg-[#111]">
      <span className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${cfg.dot}`} />
      <span className={`text-sm font-medium ${cfg.color}`}>{cfg.label}</span>
    </div>
  )
}

function ScoreBar({ label, score, reasoning }) {
  const pct = `${(score / 10) * 100}%`
  return (
    <div className="mb-3">
      <div className="flex justify-between text-xs text-gray-400 mb-1">
        <span>{label}</span>
        <span className="font-mono text-white">{score}/10</span>
      </div>
      <div className="h-1.5 bg-[#1a1a1a] w-full">
        <div
          className="h-full bg-[#FF4500] transition-all duration-700"
          style={{ width: pct }}
        />
      </div>
      {reasoning && <p className="text-gray-500 text-[11px] mt-1">{reasoning}</p>}
    </div>
  )
}

function LaunchBadge({ recommendation }) {
  const cfg = {
    'Ready to test':      { bg: 'bg-green-900 border-green-700 text-green-300' },
    'Revise before launch': { bg: 'bg-yellow-900 border-yellow-700 text-yellow-300' },
    'Do not run':         { bg: 'bg-red-900 border-red-700 text-red-300' },
  }[recommendation] || { bg: 'bg-gray-800 border-gray-700 text-gray-300' }

  return (
    <span className={`text-xs font-semibold px-3 py-1 border ${cfg.bg}`}>
      {recommendation}
    </span>
  )
}

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false)
  const handleClick = () => {
    copyToClipboard(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }
  return (
    <button
      onClick={handleClick}
      className="text-[10px] px-2 py-0.5 bg-[#1a1a1a] border border-[#2a2a2a] text-gray-400 hover:text-white hover:border-gray-500 transition-colors flex-shrink-0"
    >
      {copied ? 'Copied' : 'Copy'}
    </button>
  )
}

function QASection({ qa }) {
  if (!qa) return null
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-4">
        <div>
          <div className="text-3xl font-bold text-white font-mono">{qa.overall_score}</div>
          <div className="text-xs text-gray-500">Overall score</div>
        </div>
        <LaunchBadge recommendation={qa.launch_recommendation} />
      </div>

      <ScoreBar
        label="Hook Score"
        score={qa.hook_score?.score || 0}
        reasoning={qa.hook_score?.reasoning}
      />
      <ScoreBar
        label="Awareness Match"
        score={qa.awareness_match_score?.score || 0}
        reasoning={qa.awareness_match_score?.reasoning}
      />
      <ScoreBar
        label="Specificity"
        score={qa.specificity_score?.score || 0}
        reasoning={qa.specificity_score?.reasoning}
      />

      {qa.recommended_headline && (
        <div className="bg-[#0f1a0f] border border-green-900 p-3">
          <div className="text-xs text-green-400 font-medium mb-1 uppercase tracking-wider">
            Recommended Headline
          </div>
          <div className="text-white text-sm font-medium">{qa.recommended_headline.headline}</div>
          <div className="text-gray-500 text-xs mt-1">{qa.recommended_headline.reasoning}</div>
        </div>
      )}

      {qa.copy_violations?.length > 0 && (
        <div>
          <div className="text-xs text-gray-400 mb-1.5 uppercase tracking-wider">Copy Violations</div>
          <div className="flex flex-wrap gap-1.5">
            {qa.copy_violations.map((v, i) => (
              <span key={i} className="text-[10px] px-2 py-0.5 bg-red-950 border border-red-800 text-red-300">
                {v}
              </span>
            ))}
          </div>
        </div>
      )}

      {qa.compliance_flags?.length > 0 && (
        <div>
          <div className="text-xs text-gray-400 mb-1.5 uppercase tracking-wider">Compliance Flags</div>
          <div className="flex flex-wrap gap-1.5">
            {qa.compliance_flags.map((f, i) => (
              <span key={i} className="text-[10px] px-2 py-0.5 bg-yellow-950 border border-yellow-800 text-yellow-300">
                {f}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function CopySection({ copyPkg, bestHeadline }) {
  const [variantIdx, setVariantIdx] = useState(0)
  if (!copyPkg) return null

  const headlines = copyPkg.headlines || []
  const variants = copyPkg.primary_text_variants || []
  const hooks = copyPkg.hook_sentences || []
  const frames = copyPkg.tiktok_slideshow_frames || []
  const ctas = copyPkg.ctas || []

  return (
    <div className="space-y-6">
      {/* Headlines */}
      <div>
        <div className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">Headlines</div>
        <div className="space-y-1.5">
          {headlines.map((h, i) => (
            <div
              key={i}
              className={`flex items-center justify-between gap-3 px-3 py-2 border ${
                h === bestHeadline
                  ? 'border-[#FF4500] bg-[#1a1110]'
                  : 'border-[#2a2a2a] bg-[#111]'
              }`}
            >
              <span className="text-sm text-white">{h}</span>
              <div className="flex items-center gap-1.5">
                {h === bestHeadline && (
                  <span className="text-[10px] text-[#FF4500]">★ QA pick</span>
                )}
                <CopyButton text={h} />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* CTAs */}
      {ctas.length > 0 && (
        <div>
          <div className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">CTAs</div>
          <div className="space-y-1.5">
            {ctas.map((c, i) => (
              <div key={i} className="flex items-center justify-between gap-3 px-3 py-2 border border-[#2a2a2a] bg-[#111]">
                <span className="text-sm text-white">{c}</span>
                <CopyButton text={c} />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Primary text */}
      {variants.length > 0 && (
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="text-xs font-medium text-gray-400 uppercase tracking-wider">Primary Text</div>
            <div className="flex gap-1">
              {variants.map((_, i) => (
                <button
                  key={i}
                  onClick={() => setVariantIdx(i)}
                  className={`text-[10px] px-2 py-0.5 border transition-colors ${
                    variantIdx === i
                      ? 'bg-[#FF4500] text-white border-[#FF4500]'
                      : 'bg-transparent text-gray-500 border-[#2a2a2a] hover:text-white'
                  }`}
                >
                  V{i + 1}
                </button>
              ))}
            </div>
            <CopyButton text={variants[variantIdx] || ''} />
          </div>
          <div className="bg-[#111] border border-[#2a2a2a] p-4 text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">
            {variants[variantIdx]}
          </div>
        </div>
      )}

      {/* Hook sentences */}
      {hooks.length > 0 && (
        <div>
          <div className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">Hook Sentences</div>
          <div className="space-y-1.5">
            {hooks.map((h, i) => (
              <div key={i} className="flex items-center justify-between gap-3 px-3 py-2 border border-[#2a2a2a] bg-[#111]">
                <span className="text-sm text-gray-300 italic">"{h}"</span>
                <CopyButton text={h} />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TikTok frames */}
      {frames.length > 0 && (
        <div>
          <div className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">TikTok Slideshow Frames</div>
          <div className="flex gap-3 overflow-x-auto pb-2">
            {frames.map((f, i) => (
              <div
                key={i}
                className="flex-shrink-0 w-40 bg-black border border-[#2a2a2a] p-3 aspect-[9/16] flex flex-col justify-between"
              >
                <div className="text-[10px] text-[#FF4500] font-mono">{i + 1}/7</div>
                <div className="text-[11px] text-white leading-tight">{f.replace(/^Frame \d+: /, '')}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function CreativesSection({ brief, images, campaignId, angleName }) {
  const [briefOpen, setBriefOpen] = useState(false)

  const angleSlug = slugify(angleName || '')
  const formats = ['meta_feed', 'meta_story', 'tiktok']
  const formatLabels = { meta_feed: 'Meta Feed (1:1)', meta_story: 'Meta Story (9:16)', tiktok: 'TikTok (9:16)' }

  const imageData = images?.[angleSlug] || {}

  const downloadZip = async () => {
    try {
      const { default: JSZip } = await import('jszip')
      const { saveAs } = await import('file-saver')
      const zip = new JSZip()
      const folder = zip.folder(angleSlug)

      await Promise.all(
        formats.map(async (fmt) => {
          const src = imageData[fmt]
          if (!src || typeof src !== 'string' || src.includes('error')) return
          try {
            const resp = await fetch(src)
            const blob = await resp.blob()
            folder.file(`${fmt}.png`, blob)
          } catch {}
        })
      )

      const blob = await zip.generateAsync({ type: 'blob' })
      saveAs(blob, `adforge-${angleSlug}.zip`)
    } catch (err) {
      console.error('ZIP download failed:', err)
    }
  }

  return (
    <div className="space-y-4">
      {/* Images */}
      <div className="flex gap-4 items-end">
        {formats.map((fmt) => {
          const src = imageData[fmt]
          const hasImage = src && typeof src === 'string' && !src.includes('error')
          return (
            <div key={fmt} className="flex flex-col gap-1.5">
              <div
                className={`bg-[#111] border border-[#2a2a2a] overflow-hidden ${
                  fmt === 'meta_feed' ? 'w-40 h-40' : 'w-28 h-52'
                }`}
              >
                {hasImage ? (
                  <img src={src} alt={fmt} className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-gray-600 text-xs text-center p-2">
                    {typeof src === 'object' ? src?.error : 'Not generated'}
                  </div>
                )}
              </div>
              <div className="text-[10px] text-gray-500 text-center">{formatLabels[fmt]}</div>
              {hasImage && (
                <a
                  href={src}
                  download={`${fmt}.png`}
                  target="_blank"
                  rel="noreferrer"
                  className="text-[10px] text-center text-gray-500 hover:text-white border border-[#2a2a2a] hover:border-gray-500 py-0.5 transition-colors"
                >
                  Download
                </a>
              )}
            </div>
          )
        })}
        <button
          onClick={downloadZip}
          className="text-xs px-3 py-1.5 border border-[#2a2a2a] text-gray-400 hover:text-white hover:border-gray-500 transition-colors self-end"
        >
          Download All (ZIP)
        </button>
      </div>

      {/* Creative brief collapsible */}
      {brief && (
        <div className="border border-[#2a2a2a]">
          <button
            onClick={() => setBriefOpen((o) => !o)}
            className="w-full flex justify-between items-center px-4 py-2.5 text-xs text-gray-400 hover:text-white"
          >
            <span>Creative Brief</span>
            <span>{briefOpen ? '▲' : '▼'}</span>
          </button>
          {briefOpen && (
            <div className="px-4 pb-4 space-y-3 border-t border-[#2a2a2a] pt-3 text-xs">
              <div>
                <span className="text-gray-500">Visual Style: </span>
                <span className="text-gray-200">{brief.visual_style}</span>
              </div>
              <div>
                <span className="text-gray-500">Layout: </span>
                <span className="text-gray-200">{brief.layout_type}</span>
              </div>
              <div>
                <span className="text-gray-500">Reference: </span>
                <span className="text-gray-200">{brief.reference_aesthetic}</span>
              </div>
              {brief.color_mood && (
                <div>
                  <div className="text-gray-500 mb-1.5">Color Palette</div>
                  <div className="flex gap-2 items-center">
                    {['primary', 'secondary', 'accent'].map((k) => (
                      <div key={k} className="flex flex-col items-center gap-1">
                        <div
                          className="w-8 h-8 border border-[#2a2a2a]"
                          style={{ background: brief.color_mood[k] }}
                        />
                        <span className="font-mono text-[9px] text-gray-600">
                          {brief.color_mood[k]}
                        </span>
                      </div>
                    ))}
                    <p className="text-gray-500 text-[10px] ml-2">{brief.color_mood.rationale}</p>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ─── Main page ───────────────────────────────────────────────────────────────

const SECTION_TABS = ['QA', 'Copy', 'Creatives']

export default function CampaignOutput() {
  const { id } = useParams()
  const [campaign, setCampaign] = useState(null)
  const [activeAngle, setActiveAngle] = useState(0)
  const [activeSection, setActiveSection] = useState('QA')
  const pollRef = useRef(null)

  const loadCampaign = () => {
    fetch(`/api/campaigns/${id}`)
      .then((r) => r.json())
      .then((c) => {
        setCampaign(c)
        if (c.status === 'running' || c.status === 'pending') {
          pollRef.current = setTimeout(loadCampaign, 3000)
        }
      })
      .catch(console.error)
  }

  useEffect(() => {
    loadCampaign()
    return () => clearTimeout(pollRef.current)
  }, [id])

  if (!campaign) {
    return (
      <div className="p-6 text-gray-500 text-sm">Loading campaign…</div>
    )
  }

  const output = campaign.output ? JSON.parse(campaign.output) : null
  const angles = output?.copy_output?.angles || []
  const qaAngles = output?.qa_output?.angles || []
  const briefs = output?.creative_brief_output?.briefs || []
  const images = output?.image_output || {}
  const modelsUsed = output?.models_used || {}

  const currentCopy = angles[activeAngle]
  const currentQA = qaAngles[activeAngle]
  const currentBrief = briefs[activeAngle]
  const strategyAngles = output?.strategy_output?.angles || []

  return (
    <div className="flex flex-col h-full">
      {/* Status bar */}
      <StatusBar status={campaign.status} />

      {/* Header */}
      <div className="px-6 py-4 border-b border-[#2a2a2a]">
        <h1 className="text-lg font-semibold text-white">{campaign.name}</h1>
        <p className="text-gray-500 text-xs mt-0.5">
          {campaign.product_name} · Stage {campaign.awareness_stage} · {campaign.emotional_driver}
        </p>
      </div>

      {campaign.status === 'running' || campaign.status === 'pending' ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="w-8 h-8 rounded-full bg-[#FF4500] pulse-orange mx-auto mb-4" />
            <p className="text-gray-400 text-sm">Pipeline running…</p>
            <p className="text-gray-600 text-xs mt-1">This takes 5–15 minutes</p>
          </div>
        </div>
      ) : campaign.status === 'failed' ? (
        <div className="p-6 text-red-400 text-sm">Pipeline failed. Check server logs.</div>
      ) : output ? (
        <div className="flex-1 overflow-hidden flex flex-col">
          {/* Angle tabs */}
          {angles.length > 0 && (
            <div className="flex border-b border-[#2a2a2a] px-6 gap-0 overflow-x-auto flex-shrink-0">
              {angles.map((a, i) => (
                <button
                  key={i}
                  onClick={() => setActiveAngle(i)}
                  className={`px-4 py-3 text-xs font-medium border-b-2 transition-colors whitespace-nowrap ${
                    activeAngle === i
                      ? 'text-white border-[#FF4500]'
                      : 'text-gray-500 border-transparent hover:text-gray-300'
                  }`}
                >
                  {a.angle_name || `Angle ${i + 1}`}
                </button>
              ))}
            </div>
          )}

          {/* Section tabs */}
          <div className="flex border-b border-[#2a2a2a] px-6 gap-0 flex-shrink-0">
            {SECTION_TABS.map((s) => (
              <button
                key={s}
                onClick={() => setActiveSection(s)}
                className={`px-4 py-2.5 text-xs font-medium border-b-2 transition-colors ${
                  activeSection === s
                    ? 'text-white border-[#FF4500]'
                    : 'text-gray-500 border-transparent hover:text-gray-300'
                }`}
              >
                {s}
              </button>
            ))}
          </div>

          {/* Content area */}
          <div className="flex-1 overflow-y-auto p-6">
            {activeSection === 'QA' && <QASection qa={currentQA} />}
            {activeSection === 'Copy' && (
              <CopySection
                copyPkg={currentCopy}
                bestHeadline={currentQA?.recommended_headline?.headline}
              />
            )}
            {activeSection === 'Creatives' && (
              <CreativesSection
                brief={currentBrief}
                images={images}
                campaignId={id}
                angleName={currentCopy?.angle_name || `Angle ${activeAngle + 1}`}
              />
            )}
          </div>

          {/* Model info footer */}
          {Object.keys(modelsUsed).length > 0 && (
            <div className="border-t border-[#2a2a2a] px-6 py-2 flex-shrink-0">
              <div className="flex flex-wrap gap-3 text-[10px] text-gray-600">
                {Object.entries(modelsUsed).map(([task, model]) => (
                  <span key={task}>
                    <span className="text-gray-500 capitalize">{task}:</span>{' '}
                    <span className="font-mono">{model}</span>
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="p-6 text-gray-500 text-sm">No output yet.</div>
      )}
    </div>
  )
}
