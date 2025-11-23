import React, { useState } from 'react';
import { aiService, BuildAnalysisResult } from '../services/ai.service';

const AiBuildLab: React.FC = () => {
  const [specId, setSpecId] = useState<string>('');
  const [traitIds, setTraitIds] = useState<string>('');
  const [skillIds, setSkillIds] = useState<string>('');
  const [context, setContext] = useState<string>('WvW Zerg');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<BuildAnalysisResult | null>(null);

  const parseIds = (value: string, label: string): number[] => {
    const parts = value
      .split(',')
      .map((p) => p.trim())
      .filter((p) => p.length > 0);

    const numbers: number[] = [];
    for (const part of parts) {
      const n = Number(part);
      if (!Number.isFinite(n)) {
        throw new Error(`Veuillez entrer une liste d'IDs ${label} valide (ex: 2057, 2058).`);
      }
      numbers.push(n);
    }

    return numbers;
  };

  const getScoreClasses = (score?: string): string => {
    switch (score) {
      case 'S':
        return 'bg-amber-500 text-amber-950';
      case 'A':
        return 'bg-emerald-500 text-emerald-950';
      case 'B':
        return 'bg-sky-500 text-sky-950';
      case 'C':
        return 'bg-slate-500 text-slate-50';
      default:
        return 'bg-slate-700 text-slate-50';
    }
  };

  const handleAnalyze = async () => {
    setError(null);
    setResult(null);

    let specIdValue: number | null = null;
    const trimmedSpec = specId.trim();
    if (trimmedSpec.length > 0) {
      const n = Number(trimmedSpec);
      if (!Number.isFinite(n)) {
        setError("Veuillez entrer un ID de spécialisation valide ou laisser vide.");
        return;
      }
      specIdValue = n;
    }

    let traitIdList: number[] = [];
    let skillIdList: number[] = [];

    try {
      traitIdList = parseIds(traitIds, 'de traits');
      skillIdList = parseIds(skillIds, 'de skills');
    } catch (parseError: unknown) {
      setError(parseError instanceof Error ? parseError.message : 'Erreur dans les IDs fournis.');
      return;
    }

    try {
      setLoading(true);
      const data = await aiService.analyzeBuild(specIdValue, traitIdList, skillIdList, context);
      setResult(data);
    } catch (err: unknown) {
      const message = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Erreur lors de l'analyse du build.";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-white">AI Build Lab · Analyse de synergie de build</h1>
          <p className="text-sm text-slate-400 mt-1">
            Entrez une spécialisation, des traits et des skills pour analyser leur synergie en WvW.
          </p>
        </div>
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-4 space-y-4">
        <div className="grid gap-4 md:grid-cols-4 items-end">
          <div className="space-y-1">
            <label className="text-sm font-medium text-slate-200">ID de spécialisation (optionnel)</label>
            <input
              type="number"
              value={specId}
              onChange={(e) => setSpecId(e.target.value)}
              className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-600"
              placeholder="ex: 62"
            />
          </div>
          <div className="space-y-1">
            <label className="text-sm font-medium text-slate-200">Trait IDs</label>
            <input
              type="text"
              value={traitIds}
              onChange={(e) => setTraitIds(e.target.value)}
              className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-600"
              placeholder="ex: 2057, 2058, 2059"
            />
          </div>
          <div className="space-y-1">
            <label className="text-sm font-medium text-slate-200">Skill IDs</label>
            <input
              type="text"
              value={skillIds}
              onChange={(e) => setSkillIds(e.target.value)}
              className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-600"
              placeholder="ex: 9153, 9154, 9155"
            />
          </div>
          <div className="space-y-1">
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
          {loading ? 'Analyse en cours…' : 'Analyser la synergie'}
        </button>
        {error && <p className="text-sm text-red-400 mt-1">{error}</p>}
      </div>

      <div className="space-y-3">
        <h2 className="text-sm font-medium text-slate-200">Résultat</h2>
        {!result && !error && (
          <p className="text-sm text-slate-500">
            Aucun résultat pour le moment. Lancez une analyse pour voir le détail.
          </p>
        )}
        {result && (
          <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-4 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="space-y-1">
                <p className="text-xs uppercase tracking-wide text-slate-400">Contexte</p>
                <p className="text-sm font-semibold text-slate-50">{result.context ?? context}</p>
              </div>
              {result.synergy_score && (
                <div className="flex items-center gap-3">
                  <span className="text-xs uppercase tracking-wide text-slate-400">Score de synergie</span>
                  <span
                    className={`inline-flex items-center justify-center rounded-full px-4 py-2 text-lg font-semibold ${getScoreClasses(
                      result.synergy_score,
                    )}`}
                  >
                    {result.synergy_score}
                  </span>
                </div>
              )}
            </div>

            {Array.isArray(result.strengths) && result.strengths.length > 0 && (
              <div>
                <p className="text-xs uppercase tracking-wide text-slate-400 mb-1">Forces</p>
                <ul className="list-disc list-inside text-sm text-slate-200 space-y-1">
                  {result.strengths.map((s, idx) => (
                    <li key={idx}>{s}</li>
                  ))}
                </ul>
              </div>
            )}

            {Array.isArray(result.weaknesses) && result.weaknesses.length > 0 && (
              <div>
                <p className="text-xs uppercase tracking-wide text-slate-400 mb-1">Faiblesses</p>
                <ul className="list-disc list-inside text-sm text-slate-200 space-y-1">
                  {result.weaknesses.map((w, idx) => (
                    <li key={idx}>{w}</li>
                  ))}
                </ul>
              </div>
            )}

            {result.summary && (
              <div>
                <p className="text-xs uppercase tracking-wide text-slate-400 mb-1">Résumé</p>
                <p className="text-sm text-slate-200">{result.summary}</p>
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

export default AiBuildLab;
