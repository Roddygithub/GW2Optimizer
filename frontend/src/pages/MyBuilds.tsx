import React, { useEffect, useState } from 'react';
import { savedBuildsService, type SavedBuild } from '../services/savedBuilds.service';

const MyBuilds: React.FC = () => {
  const [builds, setBuilds] = useState<SavedBuild[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadBuilds = async () => {
    setError(null);
    setLoading(true);
    try {
      const data = await savedBuildsService.list();
      setBuilds(data);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Erreur lors du chargement de vos builds sauvegardés.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadBuilds();
  }, []);

  const handleDelete = async (id: number) => {
    if (!window.confirm('Supprimer ce build sauvegardé ?')) return;
    try {
      await savedBuildsService.delete(id);
      setBuilds((prev) => prev.filter((b) => b.id !== id));
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Erreur lors de la suppression du build.";
      setError(msg);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-white">Mes Builds</h1>
          <p className="text-sm text-slate-400 mt-1">Bibliothèque de vos builds sauvegardés depuis le Build Lab.</p>
        </div>
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-4 space-y-3">
        {loading && <p className="text-sm text-slate-300">Chargement…</p>}
        {error && <p className="text-sm text-red-400">{error}</p>}
        {!loading && !error && builds.length === 0 && (
          <p className="text-sm text-slate-500">Vous n'avez encore aucun build sauvegardé.</p>
        )}

        {!loading && !error && builds.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm text-left text-slate-200">
              <thead className="bg-slate-800/80 text-xs uppercase text-slate-400">
                <tr>
                  <th className="px-3 py-2">Nom</th>
                  <th className="px-3 py-2">Profession</th>
                  <th className="px-3 py-2">Spécialisation</th>
                  <th className="px-3 py-2">Mode de jeu</th>
                  <th className="px-3 py-2">Score</th>
                  <th className="px-3 py-2">Créé le</th>
                  <th className="px-3 py-2 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {builds.map((b) => (
                  <tr key={b.id} className="hover:bg-slate-800/40">
                    <td className="px-3 py-2 font-medium text-slate-50">
                      <div className="flex flex-col gap-0.5">
                        <span>{b.name}</span>
                        {b.source_url && (
                          <a
                            href={b.source_url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-xs font-normal text-indigo-400 hover:text-indigo-300 hover:underline break-all"
                          >
                            Source
                          </a>
                        )}
                      </div>
                    </td>
                    <td className="px-3 py-2">{b.profession ?? '—'}</td>
                    <td className="px-3 py-2">{b.specialization ?? '—'}</td>
                    <td className="px-3 py-2">{b.game_mode ?? '—'}</td>
                    <td className="px-3 py-2">
                      {b.synergy_score ? (
                        <span className="inline-flex items-center rounded-full bg-indigo-600/20 border border-indigo-500/40 px-2 py-0.5 text-xs font-semibold text-indigo-300">
                          {b.synergy_score}
                        </span>
                      ) : (
                        '—'
                      )}
                    </td>
                    <td className="px-3 py-2 text-slate-400 text-xs">
                      {new Date(b.created_at).toLocaleString()}
                    </td>
                    <td className="px-3 py-2 text-right">
                      <button
                        type="button"
                        onClick={() => void handleDelete(b.id)}
                        className="inline-flex items-center rounded-md border border-red-500/60 px-2 py-1 text-xs font-medium text-red-300 hover:bg-red-500/10"
                      >
                        Supprimer
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default MyBuilds;
