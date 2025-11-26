import React from 'react';

import type { MetaProfession } from '../../services/meta.service';

interface ProfessionChartProps {
  title?: string;
  professions: MetaProfession[];
  loading?: boolean;
}

const ProfessionChart: React.FC<ProfessionChartProps> = ({ title = 'Popularité des professions', professions, loading }) => {
  if (loading) {
    return (
      <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-4">
        <p className="text-xs uppercase tracking-wide text-slate-400 mb-2">{title}</p>
        <div className="space-y-2">
          <div className="h-3 rounded-full bg-slate-800 animate-pulse" />
          <div className="h-3 rounded-full bg-slate-800 animate-pulse" />
          <div className="h-3 rounded-full bg-slate-800 animate-pulse" />
        </div>
      </div>
    );
  }

  if (!professions.length) {
    return (
      <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-4">
        <p className="text-xs uppercase tracking-wide text-slate-400 mb-2">{title}</p>
        <p className="text-sm text-slate-500">Aucune donnée disponible pour ce mode de jeu.</p>
      </div>
    );
  }

  const maxRatio = Math.max(...professions.map((p) => p.ratio || 0), 0.01);

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-4">
      <p className="text-xs uppercase tracking-wide text-slate-400 mb-2">{title}</p>
      <div className="space-y-3">
        {professions.map((p) => {
          const widthPct = Math.max((p.ratio / maxRatio) * 100, 5);
          return (
            <div key={p.profession} className="space-y-1">
              <div className="flex items-center justify-between text-xs text-slate-300">
                <span>{p.profession}</span>
                <span className="tabular-nums text-slate-400">
                  {(p.ratio * 100).toFixed(1)}% · {p.count}
                </span>
              </div>
              <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-indigo-500 via-violet-500 to-emerald-500"
                  style={{ width: `${widthPct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ProfessionChart;

