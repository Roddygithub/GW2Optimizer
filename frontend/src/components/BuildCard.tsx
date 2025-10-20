import { Shield, Star } from 'lucide-react'

interface BuildCardProps {
  profession: string
  role: string
  gameMode: string
  description: string
  rating?: number
}

export default function BuildCard({ profession, role, gameMode, description, rating = 8.5 }: BuildCardProps) {
  return (
    <div className="bg-slate-800/50 backdrop-blur rounded-lg border border-slate-700 hover:border-gw2-gold/50 transition p-6">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-lg bg-gw2-gold/20 flex items-center justify-center">
            <Shield className="w-6 h-6 text-gw2-gold" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">{profession}</h3>
            <p className="text-sm text-gray-400">{role} · {gameMode}</p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
          <span className="text-sm font-bold text-white">{rating}</span>
        </div>
      </div>
      
      <p className="text-gray-300 text-sm mb-4">{description}</p>
      
      <div className="flex gap-2">
        <button className="flex-1 px-4 py-2 bg-gw2-blue hover:bg-gw2-blue/80 text-white text-sm rounded transition">
          View Details
        </button>
        <button className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white text-sm rounded transition">
          Copy Link
        </button>
      </div>
    </div>
  )
}
