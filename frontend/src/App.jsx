import { useEffect, useState } from 'react'
import { BrowserRouter, Link, Route, Routes, useLocation } from 'react-router-dom'
import AvatarBuilder from './pages/AvatarBuilder.jsx'
import CampaignBuilder from './pages/CampaignBuilder.jsx'
import CampaignOutput from './pages/CampaignOutput.jsx'

const NAV_ITEMS = [
  { path: '/avatars', label: 'Avatars' },
  { path: '/campaigns', label: 'Campaigns' },
]

function ModelStatusIndicator() {
  const [status, setStatus] = useState(null)

  useEffect(() => {
    fetch('/api/models/status')
      .then((r) => r.json())
      .then(setStatus)
      .catch(() => {})
  }, [])

  if (!status) return null

  return (
    <div className="px-4 pb-6 group relative">
      <div className="flex items-center gap-2 text-xs text-gray-400">
        <span
          className={`w-2 h-2 rounded-full flex-shrink-0 ${
            status.ollama_available ? 'bg-green-500' : 'bg-yellow-500'
          }`}
        />
        <span>{status.ollama_available ? 'Local models active' : 'Cloud only mode'}</span>
      </div>

      {/* Tooltip */}
      <div className="absolute bottom-full left-0 mb-2 hidden group-hover:block z-50 w-64 bg-[#1a1a1a] border border-[#2a2a2a] p-3 text-xs text-gray-300">
        <div className="font-medium text-white mb-2">Model routing</div>
        {status.model_config &&
          Object.entries(status.model_config).map(([task, cfg]) => (
            <div key={task} className="flex justify-between py-0.5">
              <span className="text-gray-400">{task}</span>
              <span className="text-gray-200 font-mono text-[10px]">{cfg.model}</span>
            </div>
          ))}
      </div>
    </div>
  )
}

function Sidebar() {
  const location = useLocation()

  return (
    <aside className="w-56 flex-shrink-0 bg-[#111111] border-r border-[#2a2a2a] flex flex-col h-full">
      <div className="px-4 py-5 border-b border-[#2a2a2a]">
        <div className="flex items-center gap-2">
          <span className="text-[#FF4500] font-bold text-lg tracking-tight">AdForge</span>
          <span className="text-gray-600 text-xs font-mono">v1</span>
        </div>
        <div className="text-gray-500 text-xs mt-0.5">Agentic Ad Creative System</div>
      </div>

      <nav className="flex-1 py-4">
        {NAV_ITEMS.map((item) => {
          const active = location.pathname.startsWith(item.path)
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center px-4 py-2.5 text-sm font-medium transition-colors ${
                active
                  ? 'text-white bg-[#1a1a1a] border-l-2 border-[#FF4500]'
                  : 'text-gray-400 hover:text-white hover:bg-[#161616] border-l-2 border-transparent'
              }`}
            >
              {item.label}
            </Link>
          )
        })}
      </nav>

      <ModelStatusIndicator />
    </aside>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex h-screen overflow-hidden bg-[#0a0a0a]">
        <Sidebar />
        <main className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/" element={<AvatarBuilder />} />
            <Route path="/avatars" element={<AvatarBuilder />} />
            <Route path="/campaigns" element={<CampaignBuilder />} />
            <Route path="/campaigns/:id/output" element={<CampaignOutput />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
