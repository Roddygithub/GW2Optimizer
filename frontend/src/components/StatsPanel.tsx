import { useQuery } from '@tanstack/react-query'
import { BarChart3, Database, TrendingUp, Award } from 'lucide-react'

export default function StatsPanel() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['learningStats'],
    queryFn: async () => {
      const response = await fetch('/api/v1/learning/stats')
      return response.json()
    }
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-12 h-12 border-4 border-gw2-gold border-t-transparent rounded-full" />
      </div>
    )
  }

  const statCards = [
    {
      icon: Database,
      label: 'Total Builds',
      value: stats?.total_datapoints || 0,
      color: 'text-blue-400'
    },
    {
      icon: Award,
      label: 'Validated Builds',
      value: stats?.validated_datapoints || 0,
      color: 'text-green-400'
    },
    {
      icon: TrendingUp,
      label: 'Avg Quality Score',
      value: stats?.average_quality_score?.toFixed(1) || '0.0',
      color: 'text-yellow-400'
    },
    {
      icon: BarChart3,
      label: 'High Quality',
      value: stats?.high_quality_count || 0,
      color: 'text-purple-400'
    }
  ]

  return (
    <div>
      <h2 className="text-2xl font-bold text-white mb-6">Learning System Statistics</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {statCards.map(({ icon: Icon, label, value, color }) => (
          <div key={label} className="bg-slate-800/50 backdrop-blur rounded-lg border border-slate-700 p-6">
            <div className="flex items-center gap-3 mb-2">
              <Icon className={`w-6 h-6 ${color}`} />
              <p className="text-gray-400 text-sm">{label}</p>
            </div>
            <p className="text-3xl font-bold text-white">{value}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-slate-800/50 backdrop-blur rounded-lg border border-slate-700 p-6">
          <h3 className="text-lg font-bold text-white mb-4">Quality Distribution</h3>
          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-400">High Quality (≥8)</span>
                <span className="text-green-400">{stats?.high_quality_count || 0}</span>
              </div>
              <div className="w-full bg-slate-700 rounded-full h-2">
                <div 
                  className="bg-green-500 h-2 rounded-full transition-all"
                  style={{ width: `${(stats?.high_quality_count / (stats?.total_datapoints || 1)) * 100}%` }}
                />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-400">Medium Quality (5-8)</span>
                <span className="text-yellow-400">{stats?.medium_quality_count || 0}</span>
              </div>
              <div className="w-full bg-slate-700 rounded-full h-2">
                <div 
                  className="bg-yellow-500 h-2 rounded-full transition-all"
                  style={{ width: `${(stats?.medium_quality_count / (stats?.total_datapoints || 1)) * 100}%` }}
                />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-400">Low Quality (&lt;5)</span>
                <span className="text-red-400">{stats?.low_quality_count || 0}</span>
              </div>
              <div className="w-full bg-slate-700 rounded-full h-2">
                <div 
                  className="bg-red-500 h-2 rounded-full transition-all"
                  style={{ width: `${(stats?.low_quality_count / (stats?.total_datapoints || 1)) * 100}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        <div className="bg-slate-800/50 backdrop-blur rounded-lg border border-slate-700 p-6">
          <h3 className="text-lg font-bold text-white mb-4">Data Sources</h3>
          <div className="space-y-2">
            {Object.entries(stats?.datapoints_by_source || {}).map(([source, count]) => (
              <div key={source} className="flex justify-between items-center py-2 border-b border-slate-700 last:border-0">
                <span className="text-gray-300 capitalize">{source.replace('_', ' ')}</span>
                <span className="text-gw2-gold font-bold">{count as number}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
