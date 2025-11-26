import React from 'react';

import type { MetaArchetype } from '../../services/meta.service';

interface ArchetypeListProps {
  title?: string;
  archetypes: MetaArchetype[];
  loading?: boolean;
}

const ArchetypeList: React.FC<ArchetypeListProps> = ({ title = 'Top archétypes', archetypes, loading }) => {
  if (loading) {
    return (
      <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-4">
        <p className="text-xs uppercase tracking-wide text-slate-400 mb-2">{title}</p>
        <div className="space-y-2">
          <div className="h-4 rounded bg-slate-800 animate-pulse" />
          <div className="h-4 rounded bg-slate-800 animate-pulse" />
          <div className="h-4 rounded bg-slate-800 animate-pulse" />
        </div>
      </div>
    );
  }

  if (!archetypes.length) {
    return (
      <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-4">
        <p className="text-xs uppercase tracking-wide text-slate-400 mb-2">{title}</p>
        <p className="text-sm text-slate-500">Aucun archétype enregistré pour ce mode de jeu.</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-4">
      <p className="text-xs uppercase tracking-wide text-slate-400 mb-3">{title}</p>
      <div className="overflow-x-auto">
        <table className="min-w-full text-xs text-left text-slate-300">
          <thead className="border-b border-slate-800 text-slate-400">
            <tr>
              <th className="py-2 pr-4">Profession</th>
              <th className="py-2 pr-4">Spécialisation</th>
              <th className="py-2 pr-4">Score</th>
              <th className="py-2 pr-4 text-right">Occurrences</th>
              <th className="py-2 pr-0 text-right">Fréquence</th>
            </tr>
          </thead>
          <tbody>
            {archetypes.map((a, index) => (
              <tr key={`${a.profession}-${a.specialization}-${index}`} className="border-b border-slate-800/60">
                <td className="py-2 pr-4 align-middle text-slate-200">{a.profession ?? 'Inconnu'}</td>
                <td className="py-2 pr-4 align-middle">{a.specialization ?? 'Inconnue'}</td>
                <td className="py-2 pr-4 align-middle">
                  <span className="inline-flex items-center rounded-full border border-slate-700 px-2 py-0.5 text-[10px] uppercase tracking-wide">
                    {a.synergy_score ?? 'N/A'}
                  </span>
                </td>
                <td className="py-2 pr-4 align-middle text-right tabular-nums">{a.occurrences}</td>
                <td className="py-2 pr-0 align-middle text-right tabular-nums text-slate-400">
                  {(a.frequency * 100).toFixed(1)}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ArchetypeList;

