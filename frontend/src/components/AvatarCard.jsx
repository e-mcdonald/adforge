const AWARENESS_LABELS = {
  1: 'Unaware',
  2: 'Problem Aware',
  3: 'Solution Aware',
  4: 'Product Aware',
  5: 'Most Aware',
}

const TRIGGER_COLORS = {
  Fear: 'bg-red-900 text-red-300 border-red-800',
  Desire: 'bg-orange-900 text-orange-300 border-orange-800',
  Curiosity: 'bg-blue-900 text-blue-300 border-blue-800',
  Belonging: 'bg-purple-900 text-purple-300 border-purple-800',
}

const STAGE_COLORS = {
  1: 'bg-gray-800 text-gray-300',
  2: 'bg-yellow-900 text-yellow-300',
  3: 'bg-blue-900 text-blue-300',
  4: 'bg-purple-900 text-purple-300',
  5: 'bg-green-900 text-green-300',
}

export default function AvatarCard({ avatar }) {
  const triggers = (avatar.emotional_triggers || '').split(',').map((t) => t.trim()).filter(Boolean)
  const stage = avatar.awareness_stage || 1

  return (
    <div className="bg-[#111111] border border-[#2a2a2a] p-4 hover:border-[#3a3a3a] transition-colors">
      <div className="flex items-start justify-between gap-3 mb-3">
        <div>
          <h3 className="font-semibold text-white text-sm">{avatar.name}</h3>
          <p className="text-gray-500 text-xs mt-0.5">{avatar.age_demo}</p>
        </div>
        <span
          className={`text-xs px-2 py-0.5 font-medium flex-shrink-0 ${STAGE_COLORS[stage]}`}
        >
          S{stage} · {AWARENESS_LABELS[stage]}
        </span>
      </div>

      <p className="text-gray-300 text-xs mb-3 leading-relaxed">{avatar.core_pain}</p>

      <div className="flex flex-wrap gap-1.5">
        {triggers.map((t) => (
          <span
            key={t}
            className={`text-[10px] px-1.5 py-0.5 border font-medium ${
              TRIGGER_COLORS[t] || 'bg-gray-800 text-gray-400 border-gray-700'
            }`}
          >
            {t}
          </span>
        ))}
        <span className="text-[10px] px-1.5 py-0.5 bg-[#1a1a1a] text-gray-500 border border-[#2a2a2a]">
          {avatar.sophistication_level}
        </span>
      </div>
    </div>
  )
}
