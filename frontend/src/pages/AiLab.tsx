import React, { useState } from 'react';
import { aiService, SkillAnalysisResult } from '../services/ai.service';

const AiLab: React.FC = () => {
  const [skillId, setSkillId] = useState<string>('');
  const [context, setContext] = useState<string>('WvW Zerg');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SkillAnalysisResult | null>(null);

  const handleAnalyze = async () => {
    setError(null);
    setResult(null);

    const id = Number(skillId);
    if (!id || Number.isNaN(id)) {
      setError('Veuillez entrer un ID de skill valide.');
      return;
    }

    try {
      setLoading(true);
      const data = await aiService.analyzeSkill(id, context);
      setResult(data);
    } catch (err: unknown) {
      const message = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Erreur lors de l'analyse du skill.";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-white">AI Lab · Analyse de compétences</h1>
          <p className="text-sm text-slate-400 mt-1">
            Entrez un ID de compétence Guild Wars 2 et un contexte. L'IA analysera sa pertinence en WvW.
          </p>
        </div>
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-4 space-y-4">
        <div className="grid gap-4 md:grid-cols-3 items-end">
          <div className="space-y-1">
            <label className="text-sm font-medium text-slate-200">ID du skill</label>
            <input
              type="number"
              value={skillId}
              onChange={(e) => setSkillId(e.target.value)}
              className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-600"
              placeholder="ex: 9153"
            />
          </div>
          <div className="space-y-1 md:col-span-2">
            <label className="text-sm font-medium text-slate-200">Contexte</label>
            <input
              type="text"
              value={context}
              onChange={(e) => setContext(e.target.value)}
              className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-600"
              placeholder="WvW Zerg, Roaming, PvE..."
            />
          </div>
        </div>
        <button
          type="button"
          onClick={handleAnalyze}
          disabled={loading}
          className="inline-flex items-center justify-center rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {loading ? 'Analyse en cours…' : 'Analyser le skill'}
        </button>
        {error && (
          <p className="text-sm text-red-400 mt-1">{error}</p>
        )}
      </div>

      <div className="space-y-3">
        <h2 className="text-sm font-medium text-slate-200">Résultat</h2>
        {!result && !error && (
          <p className="text-sm text-slate-500">Aucun résultat pour le moment. Lancez une analyse pour voir le détail.</p>
        )}
        {result && (
          <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-4 space-y-4">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <div>
                <p className="text-xs uppercase tracking-wide text-slate-400">Compétence</p>
                <p className="text-sm font-semibold text-slate-50">
                  {result.skill_name ?? 'Inconnue'}
                  {result.skill_id && (
                    <span className="ml-2 text-xs text-slate-400">(ID {result.skill_id})</span>
                  )}
                </p>
              </div>
              {result.rating && (
                <span className="inline-flex items-center rounded-full bg-indigo-600/20 border border-indigo-500/40 px-3 py-1 text-xs font-medium text-indigo-300">
                  {result.rating}
                </span>
              )}
            </div>

            {result.reason && (
              <div>
                <p className="text-xs uppercase tracking-wide text-slate-400 mb-1">Analyse</p>
                <p className="text-sm text-slate-200">{result.reason}</p>
              </div>
            )}

            {Array.isArray(result.tags) && result.tags.length > 0 && (
              <div>
                <p className="text-xs uppercase tracking-wide text-slate-400 mb-1">Tags</p>
                <div className="flex flex-wrap gap-2">
                  {result.tags.map((tag) => (
                    <span
                      key={tag}
                      className="inline-flex items-center rounded-full border border-slate-700 bg-slate-950 px-2 py-1 text-xs text-slate-200"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <details className="mt-2">
              <summary className="text-xs text-slate-500 cursor-pointer">Voir le JSON brut</summary>
              <pre className="mt-2 max-h-64 overflow-auto rounded-md bg-slate-950 p-3 text-xs text-slate-300">
                {JSON.stringify(result, null, 2)}
              </pre>
            </details>
          </div>
        )}
      </div>
    </div>
  );
};

export default AiLab;
