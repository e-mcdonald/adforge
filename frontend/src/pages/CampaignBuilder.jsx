import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

const AWARENESS_STAGES = [
  { value: 1, label: 'Unaware' },
  { value: 2, label: 'Problem Aware' },
  { value: 3, label: 'Solution Aware' },
  { value: 4, label: 'Product Aware' },
  { value: 5, label: 'Most Aware' },
]

const EMOTIONAL_DRIVERS = ['Fear', 'Desire', 'Curiosity', 'Belonging']

const COPY_MODELS = [
  { value: 'claude-opus-4-5', label: 'Claude Opus 4.5', desc: 'Best quality — recommended for copy' },
  { value: 'claude-sonnet-4-5', label: 'Claude Sonnet 4.5', desc: 'Faster, lower cost' },
  { value: 'gpt-4o', label: 'GPT-4o', desc: 'OpenAI alternative' },
]

const EMPTY_FORM = {
  name: '',
  product_name: '',
  product_url: '',
  product_price: '',
  avatar_id: '',
  angle: '',
  platform_meta_feed: false,
  platform_meta_story: false,
  platform_tiktok: false,
  awareness_stage: 1,
  emotional_driver: 'Desire',
  copy_model: 'claude-opus-4-5',
  use_local_models: true,
}

function Toast({ message, onClose }) {
  useEffect(() => {
    const t = setTimeout(onClose, 3000)
    return () => clearTimeout(t)
  }, [onClose])
  return <div className="toast">{message}</div>
}

export default function CampaignBuilder() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ ...EMPTY_FORM })
  const [avatars, setAvatars] = useState([])
  const [costEstimate, setCostEstimate] = useState('~$0.25–0.40/campaign')
  const [ollamaAvailable, setOllamaAvailable] = useState(null)
  const [modelSettingsOpen, setModelSettingsOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [toast, setToast] = useState(null)

  useEffect(() => {
    fetch('/api/avatars').then((r) => r.json()).then(setAvatars).catch(console.error)
    fetch('/api/models/status')
      .then((r) => r.json())
      .then((s) => setOllamaAvailable(s.ollama_available))
      .catch(() => {})
  }, [])

  // Auto-populate awareness/emotional from selected avatar
  useEffect(() => {
    if (!form.avatar_id) return
    const avatar = avatars.find((a) => a.id === form.avatar_id)
    if (!avatar) return
    const firstTrigger = (avatar.emotional_triggers || '').split(',')[0]?.trim() || 'Desire'
    setForm((f) => ({
      ...f,
      awareness_stage: avatar.awareness_stage,
      emotional_driver: firstTrigger,
    }))
  }, [form.avatar_id, avatars])

  // Live cost estimate
  useEffect(() => {
    const params = new URLSearchParams({
      use_local: form.use_local_models,
      copy_model: form.copy_model,
    })
    fetch(`/api/models/cost-estimate?${params}`)
      .then((r) => r.json())
      .then((d) => setCostEstimate(d.estimate))
      .catch(() => {})
  }, [form.use_local_models, form.copy_model])

  const set = (field, value) => setForm((f) => ({ ...f, [field]: value }))
  const toggle = (field) => setForm((f) => ({ ...f, [field]: !f[field] }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const resp = await fetch('/api/campaigns', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      })
      if (!resp.ok) throw new Error(await resp.text())
      const campaign = await resp.json()

      // Kick off pipeline
      await fetch(`/api/campaigns/${campaign.id}/run`, { method: 'POST' })

      navigate(`/campaigns/${campaign.id}/output`)
    } catch (err) {
      setToast(`Error: ${err.message}`)
      setLoading(false)
    }
  }

  const PlatformBtn = ({ field, label }) => (
    <button
      type="button"
      onClick={() => toggle(field)}
      className={`px-4 py-2 text-xs font-medium border transition-colors ${
        form[field]
          ? 'bg-[#FF4500] text-white border-[#FF4500]'
          : 'bg-transparent text-gray-400 border-[#2a2a2a] hover:border-gray-500 hover:text-white'
      }`}
    >
      {label}
    </button>
  )

  return (
    <div className="p-6 max-w-2xl">
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-white">Campaign Builder</h1>
        <p className="text-gray-500 text-sm mt-1">Configure your ad campaign and launch the pipeline</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Campaign name */}
        <div>
          <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">
            Campaign Name
          </label>
          <input
            className="w-full bg-[#111] border border-[#2a2a2a] text-white px-3 py-2 text-sm focus:outline-none focus:border-[#FF4500] transition-colors"
            placeholder="GlareCut Q3 Launch"
            value={form.name}
            onChange={(e) => set('name', e.target.value)}
            required
          />
        </div>

        {/* Product fields */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">
              Product Name
            </label>
            <input
              className="w-full bg-[#111] border border-[#2a2a2a] text-white px-3 py-2 text-sm focus:outline-none focus:border-[#FF4500] transition-colors"
              placeholder="GlareCut"
              value={form.product_name}
              onChange={(e) => set('product_name', e.target.value)}
              required
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">
              Price
            </label>
            <input
              className="w-full bg-[#111] border border-[#2a2a2a] text-white px-3 py-2 text-sm focus:outline-none focus:border-[#FF4500] transition-colors"
              placeholder="$39.00"
              value={form.product_price}
              onChange={(e) => set('product_price', e.target.value)}
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">
            Product URL
          </label>
          <input
            className="w-full bg-[#111] border border-[#2a2a2a] text-white px-3 py-2 text-sm focus:outline-none focus:border-[#FF4500] transition-colors"
            placeholder="https://..."
            value={form.product_url}
            onChange={(e) => set('product_url', e.target.value)}
          />
        </div>

        {/* Avatar selector */}
        <div>
          <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">
            Avatar
          </label>
          <select
            className="w-full bg-[#111] border border-[#2a2a2a] text-white px-3 py-2 text-sm focus:outline-none focus:border-[#FF4500] transition-colors"
            value={form.avatar_id}
            onChange={(e) => set('avatar_id', e.target.value)}
            required
          >
            <option value="">Select an avatar…</option>
            {avatars.map((a) => (
              <option key={a.id} value={a.id}>
                {a.name} — Stage {a.awareness_stage}
              </option>
            ))}
          </select>
        </div>

        {/* Angle */}
        <div>
          <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">
            Core Angle / Mechanism
          </label>
          <textarea
            className="w-full bg-[#111] border border-[#2a2a2a] text-white px-3 py-2 text-sm focus:outline-none focus:border-[#FF4500] transition-colors resize-none"
            rows={2}
            placeholder="The core hook or mechanism that makes this product different..."
            value={form.angle}
            onChange={(e) => set('angle', e.target.value)}
          />
        </div>

        {/* Platforms */}
        <div>
          <label className="block text-xs font-medium text-gray-400 mb-2 uppercase tracking-wider">
            Target Platforms
          </label>
          <div className="flex gap-2">
            <PlatformBtn field="platform_meta_feed" label="Meta Feed" />
            <PlatformBtn field="platform_meta_story" label="Meta Story" />
            <PlatformBtn field="platform_tiktok" label="TikTok" />
          </div>
        </div>

        {/* Awareness + Emotional Driver */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-2 uppercase tracking-wider">
              Awareness Stage
            </label>
            <div className="flex gap-1">
              {AWARENESS_STAGES.map((s) => (
                <button
                  key={s.value}
                  type="button"
                  onClick={() => set('awareness_stage', s.value)}
                  className={`flex-1 py-2 text-xs font-bold border transition-colors ${
                    form.awareness_stage === s.value
                      ? 'bg-[#FF4500] text-white border-[#FF4500]'
                      : 'bg-transparent text-gray-400 border-[#2a2a2a] hover:border-gray-500'
                  }`}
                >
                  {s.value}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-2 uppercase tracking-wider">
              Primary Emotional Driver
            </label>
            <select
              className="w-full bg-[#111] border border-[#2a2a2a] text-white px-3 py-2 text-sm focus:outline-none focus:border-[#FF4500]"
              value={form.emotional_driver}
              onChange={(e) => set('emotional_driver', e.target.value)}
            >
              {EMOTIONAL_DRIVERS.map((d) => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Model Settings (collapsible) */}
        <div className="border border-[#2a2a2a]">
          <button
            type="button"
            onClick={() => setModelSettingsOpen((o) => !o)}
            className="w-full flex items-center justify-between px-4 py-3 text-sm font-medium text-gray-300 hover:text-white"
          >
            <span>Model Settings</span>
            <span className="text-gray-600">{modelSettingsOpen ? '▲' : '▼'}</span>
          </button>

          {modelSettingsOpen && (
            <div className="px-4 pb-4 space-y-4 border-t border-[#2a2a2a]">
              <div className="pt-4">
                <label className="block text-xs font-medium text-gray-400 mb-2 uppercase tracking-wider">
                  Copy Model
                </label>
                <div className="space-y-2">
                  {COPY_MODELS.map((m) => (
                    <label
                      key={m.value}
                      className={`flex items-start gap-3 p-3 border cursor-pointer transition-colors ${
                        form.copy_model === m.value
                          ? 'border-[#FF4500] bg-[#1a1110]'
                          : 'border-[#2a2a2a] hover:border-[#3a3a3a]'
                      }`}
                    >
                      <input
                        type="radio"
                        name="copy_model"
                        value={m.value}
                        checked={form.copy_model === m.value}
                        onChange={() => set('copy_model', m.value)}
                        className="mt-0.5 accent-[#FF4500]"
                      />
                      <div>
                        <div className="text-sm font-medium text-white">{m.label}</div>
                        <div className="text-xs text-gray-500 mt-0.5">{m.desc}</div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <label className="flex items-center justify-between cursor-pointer">
                  <div>
                    <div className="text-sm font-medium text-white">Use local models for non-copy tasks</div>
                    <div className="text-xs text-gray-500 mt-0.5">Requires Ollama with llama3.1:8b</div>
                  </div>
                  <div
                    onClick={() => toggle('use_local_models')}
                    className={`w-10 h-5 relative rounded-full cursor-pointer transition-colors ${
                      form.use_local_models ? 'bg-[#FF4500]' : 'bg-[#2a2a2a]'
                    }`}
                  >
                    <span
                      className={`absolute top-0.5 w-4 h-4 bg-white rounded-full transition-all ${
                        form.use_local_models ? 'left-5' : 'left-0.5'
                      }`}
                    />
                  </div>
                </label>

                {form.use_local_models && ollamaAvailable === false && (
                  <div className="mt-2 text-xs text-yellow-500 bg-yellow-950 border border-yellow-900 px-3 py-2">
                    Ollama not detected — non-copy tasks will use gpt-4o-mini
                  </div>
                )}
              </div>

              <div className="bg-[#0f0f0f] border border-[#2a2a2a] px-4 py-3 flex items-center justify-between">
                <span className="text-xs text-gray-400">Estimated campaign cost</span>
                <span className="text-sm font-semibold text-[#FF4500]">{costEstimate}</span>
              </div>
            </div>
          )}
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-[#FF4500] text-white py-3 text-sm font-semibold hover:bg-[#e03d00] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? 'Launching pipeline…' : 'Launch Campaign Pipeline'}
        </button>
      </form>

      {toast && <Toast message={toast} onClose={() => setToast(null)} />}
    </div>
  )
}
