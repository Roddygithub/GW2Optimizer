import { useState } from 'react'
import { Shield, Users, Bot, BarChart3 } from 'lucide-react'
import ChatBox from './components/ChatBox'
import BuildCard from './components/BuildCard'
import StatsPanel from './components/StatsPanel'

function App() {
  const [activeTab, setActiveTab] = useState('chat')

  return (
    <div className="min-h-screen bg-gradient-to-br from-gw2-dark via-slate-900 to-gw2-blue">
      {/* Header */}
      <header className="bg-slate-900/80 backdrop-blur-sm border-b border-gw2-gold/20">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Shield className="w-8 h-8 text-gw2-gold" />
              <h1 className="text-2xl font-bold text-gw2-gold">GW2Optimizer</h1>
              <span className="text-sm text-gray-400">WvW Team Builder</span>
            </div>
            <div className="flex gap-2">
              <button className="px-4 py-2 bg-gw2-gold/20 hover:bg-gw2-gold/30 rounded-lg transition">
                Sign In
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-slate-800/50 border-b border-slate-700">
        <div className="container mx-auto px-4">
          <div className="flex gap-1">
            {[
              { id: 'chat', label: 'Chat', icon: Bot },
              { id: 'builds', label: 'Builds', icon: Shield },
              { id: 'teams', label: 'Teams', icon: Users },
              { id: 'stats', label: 'Stats', icon: BarChart3 },
            ].map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={`flex items-center gap-2 px-6 py-3 transition ${
                  activeTab === id
                    ? 'bg-gw2-blue text-white border-b-2 border-gw2-gold'
                    : 'text-gray-400 hover:text-white hover:bg-slate-700/50'
                }`}
              >
                <Icon className="w-4 h-4" />
                {label}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {activeTab === 'chat' && <ChatBox />}
        {activeTab === 'builds' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <BuildCard
              profession="Guardian"
              role="Support"
              gameMode="Zerg"
              description="Firebrand healer with excellent boon support"
            />
          </div>
        )}
        {activeTab === 'teams' && (
          <div className="text-center text-gray-400 py-20">
            <Users className="w-16 h-16 mx-auto mb-4 opacity-50" />
            <p>No teams created yet. Use the chat to create your first team!</p>
          </div>
        )}
        {activeTab === 'stats' && <StatsPanel />}
      </main>

      {/* Footer */}
      <footer className="bg-slate-900/80 border-t border-slate-700 mt-20">
        <div className="container mx-auto px-4 py-6 text-center text-gray-400 text-sm">
          <p>GW2Optimizer © 2025 - Powered by AI and Guild Wars 2 Community</p>
        </div>
      </footer>
    </div>
  )
}

export default App
