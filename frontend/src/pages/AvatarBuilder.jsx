import { useEffect, useState } from 'react'
import AvatarCard from '../components/AvatarCard.jsx'

const AWARENESS_STAGES = [
  { value: 1, label: 'Unaware', desc: 'Has the problem but has not named it' },
  { value: 2, label: 'Problem Aware', desc: 'Knows they have a problem, no solution yet' },
  { value: 3, label: 'Solution Aware', desc: 'Knows solutions exist, not your product' },
  { value: 4, label: 'Product Aware', desc: 'Knows your product, not convinced' },
  { value: 5, label: 'Most Aware', desc: 'Ready to buy, needs the offer' },
]

const EMOTIONAL_TRIGGERS = ['Fear', 'Desire', 'Curiosity', 'Belonging']
const SOPHISTICATION_LEVELS = ['Low', 'Medium', 'High']

const EMPTY_FORM = {
  name: '',
  age_demo: '',
  core_pain: '',
  dream_outcome: '',
  emotional_triggers: [],
  sophistication_level: 'Medium',
  existing_beliefs: '',
  raw_language: '',
  awareness_stage: 1,
}

function Toast({ message, onClose }) {
  useEffect(() => {
    const t = setTimeout(onClose, 3000)
    return () => clearTimeout(t)
  }, [onClose])
  return <div className="toast">{message}</div>
}

export default function AvatarBuilder() {
  const [form, setForm] = useState({ ...EMPTY_FORM })
  const [avatars, setAvatars] = useState([])
  const [toast, setToast] = useState(null)
  const [loading, setLoading] = useState(false)

  const loadAvatars = () => {
    fetch('/api/avatars')
      .then((r) => r.json())
      .then(setAvatars)
      .catch(console.error)
  }

  useEffect(() => {
    loadAvatars()
  }, [])

  const set = (field, value) => setForm((f) => ({ ...f, [field]: value }))

  const toggleTrigger = (t) => {
    setForm((f) => {
      const triggers = f.emotional_triggers.includes(t)
        ? f.emotional_triggers.filter((x) => x !== t)
        : [...f.emotional_triggers, t]
      return { ...f, emotional_triggers: triggers }
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const payload = {
        ...form,
        emotional_triggers: form.emotional_triggers.join(','),
      }
      const resp = await fetch('/api/avatars', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!resp.ok) throw new Error(await resp.text())
      setToast('Avatar saved successfully')
      setForm({ ...EMPTY_FORM })
      loadAvatars()
    } catch (err) {
      setToast(`Error: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex h-full">
      {/* Form panel */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-2xl">
          <div className="mb-6">
            <h1 className="text-xl font-semibold text-white">Avatar Builder</h1>
            <p className="text-gray-500 text-sm mt-1">
              Build a psychographic profile of your ideal customer
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Name + Age Demo */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">
                  Avatar Name
                </label>
                <input
                  className="w-full bg-[#111] border border-[#2a2a2a] text-white px-3 py-2 text-sm focus:outline-none focus:border-[#FF4500] transition-colors"
                  placeholder="Night Anxiety Nancy"
                  value={form.name}
                  onChange={(e) => set('name', e.target.value)}
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">
                  Age / Demo
                </label>
                <input
                  className="w-full bg-[#111] border border-[#2a2a2a] text-white px-3 py-2 text-sm focus:outline-none focus:border-[#FF4500] transition-colors"
                  placeholder="52, suburban woman"
                  value={form.age_demo}
                  onChange={(e) => set('age_demo', e.target.value)}
                  required
                />
              </div>
            </div>

            {/* Core Pain */}
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">
                Core Pain
              </label>
              <textarea
                className="w-full bg-[#111] border border-[#2a2a2a] text-white px-3 py-2 text-sm focus:outline-none focus:border-[#FF4500] transition-colors resize-none"
                rows={2}
                placeholder="The specific pain they feel daily..."
                value={form.core_pain}
                onChange={(e) => set('core_pain', e.target.value)}
                required
              />
            </div>

            {/* Dream Outcome */}
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">
                Dream Outcome
              </label>
              <textarea
                className="w-full bg-[#111] border border-[#2a2a2a] text-white px-3 py-2 text-sm focus:outline-none focus:border-[#FF4500] transition-colors resize-none"
                rows={2}
                placeholder="What they actually want..."
                value={form.dream_outcome}
                onChange={(e) => set('dream_outcome', e.target.value)}
                required
              />
            </div>

            {/* Emotional Triggers */}
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">
                Emotional Triggers
              </label>
              <div className="flex gap-2">
                {EMOTIONAL_TRIGGERS.map((t) => {
                  const selected = form.emotional_triggers.includes(t)
                  return (
                    <button
                      key={t}
                      type="button"
                      onClick={() => toggleTrigger(t)}
                      className={`px-3 py-1.5 text-xs font-medium border transition-colors ${
                        selected
                          ? 'bg-[#FF4500] text-white border-[#FF4500]'
                          : 'bg-transparent text-gray-400 border-[#2a2a2a] hover:border-gray-500 hover:text-white'
                      }`}
                    >
                      {t}
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Sophistication + Awareness */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">
                  Market Sophistication
                </label>
                <div className="flex gap-2">
                  {SOPHISTICATION_LEVELS.map((l) => (
                    <button
                      key={l}
                      type="button"
                      onClick={() => set('sophistication_level', l)}
                      className={`flex-1 py-1.5 text-xs font-medium border transition-colors ${
                        form.sophistication_level === l
                          ? 'bg-[#FF4500] text-white border-[#FF4500]'
                          : 'bg-transparent text-gray-400 border-[#2a2a2a] hover:border-gray-500 hover:text-white'
                      }`}
                    >
                      {l}
                    </button>
                  ))}
                </div>
              </div>
              <div />
            </div>

            {/* Awareness Stage */}
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-2 uppercase tracking-wider">
                Awareness Stage (Schwartz)
              </label>
              <div className="flex gap-2">
                {AWARENESS_STAGES.map((s) => (
                  <button
                    key={s.value}
                    type="button"
                    onClick={() => set('awareness_stage', s.value)}
                    className={`flex-1 text-center py-2 px-1 border transition-colors ${
                      form.awareness_stage === s.value
                        ? 'bg-[#FF4500] text-white border-[#FF4500]'
                        : 'bg-transparent text-gray-400 border-[#2a2a2a] hover:border-gray-500 hover:text-white'
                    }`}
                    title={s.desc}
                  >
                    <div className="text-sm font-bold">{s.value}</div>
                    <div className="text-[9px] mt-0.5 leading-tight">{s.label}</div>
                  </button>
                ))}
              </div>
              <p className="text-gray-600 text-xs mt-1.5">
                {AWARENESS_STAGES.find((s) => s.value === form.awareness_stage)?.desc}
              </p>
            </div>

            {/* Existing Beliefs */}
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">
                Existing Beliefs
              </label>
              <textarea
                className="w-full bg-[#111] border border-[#2a2a2a] text-white px-3 py-2 text-sm focus:outline-none focus:border-[#FF4500] transition-colors resize-none"
                rows={3}
                placeholder="What they currently believe about the problem..."
                value={form.existing_beliefs}
                onChange={(e) => set('existing_beliefs', e.target.value)}
              />
            </div>

            {/* Raw Language */}
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">
                Raw Language
              </label>
              <textarea
                className="w-full bg-[#111] border border-[#2a2a2a] text-white px-3 py-2 text-sm focus:outline-none focus:border-[#FF4500] transition-colors resize-none"
                rows={3}
                placeholder="Exact words/phrases they use — from forums, reviews, Reddit..."
                value={form.raw_language}
                onChange={(e) => set('raw_language', e.target.value)}
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-[#FF4500] text-white py-2.5 text-sm font-semibold hover:bg-[#e03d00] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Saving…' : 'Save Avatar'}
            </button>
          </form>
        </div>
      </div>

      {/* Avatar list panel */}
      <div className="w-80 flex-shrink-0 border-l border-[#2a2a2a] overflow-y-auto p-4">
        <div className="mb-4">
          <h2 className="text-sm font-medium text-gray-400 uppercase tracking-wider">
            Saved Avatars ({avatars.length})
          </h2>
        </div>
        <div className="space-y-2">
          {avatars.length === 0 && (
            <p className="text-gray-600 text-xs text-center py-8">No avatars yet</p>
          )}
          {avatars.map((a) => (
            <AvatarCard key={a.id} avatar={a} />
          ))}
        </div>
      </div>

      {toast && <Toast message={toast} onClose={() => setToast(null)} />}
    </div>
  )
}
