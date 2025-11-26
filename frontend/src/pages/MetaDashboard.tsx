import React, { useEffect, useState } from 'react';

import { metaService, type MetaOverviewResponse } from '../services/meta.service';
import ProfessionChart from '../components/meta/ProfessionChart';
import ArchetypeList from '../components/meta/ArchetypeList';

const GAME_MODES = [
  { value: 'zerg', label: 'WvW Zerg' },
  { value: 'raid', label: 'Raids' },
  { value: 'fractals', label: 'Fractales' },
  { value: 'roaming', label: 'Roaming' },
  { value: 'strikes', label: 'Strikes' },
];

const MetaDashboard: React.FC = () => {
  const [gameMode, setGameMode] = useState<string>('zerg');
  const [overview, setOverview] = useState<MetaOverviewResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const fetchOverview = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await metaService.getMetaOverview(gameMode, { timeRange: 30 });
        if (!cancelled) {
          setOverview(data);
        }
      } catch (e) {
        if (!cancelled) {
          setError('Impossible de charger les données de méta.');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    void fetchOverview();

    return () => {
      cancelled = true;
    };
  }, [gameMode]);

  const hasData = !!overview && overview.professions.length > 0;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-white">Meta Dashboard</h1>
          <p className="text-sm text-slate-400 mt-1">
            Vue d&apos;ensemble des archétypes les plus joués, basée sur les builds sauvegardés.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <label className="text-xs uppercase tracking-wide text-slate-400">Mode de jeu</label>
          <select
            className="rounded-md border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
            value={gameMode}
            onChange={(e) => setGameMode(e.target.value)}
          >
            {GAME_MODES.map((mode) => (
              <option key={mode.value} value={mode.value}>
                {mode.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && (
        <div className="rounded-md border border-red-500/40 bg-red-950/40 px-4 py-2 text-sm text-red-200">
          {error}
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-3">
        <div className="md:col-span-1">
          <ProfessionChart professions={overview?.professions ?? []} loading={loading} />
        </div>
        <div className="md:col-span-2">
          <ArchetypeList archetypes={overview?.archetypes ?? []} loading={loading} />
        </div>
      </div>

      {!loading && !error && !hasData && (
        <p className="text-xs text-slate-500">
          Aucune donnée de méta disponible pour ce mode de jeu pour l&apos;instant. Essayez de sauvegarder quelques builds
          puis revenez ici.
        </p>
      )}
    </div>
  );
};

export default MetaDashboard;

