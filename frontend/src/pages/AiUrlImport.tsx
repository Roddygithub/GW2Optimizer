import React, { useState } from 'react';
import { aiService, type UrlAnalysisResult } from '../services/ai.service';
import { savedBuildsService } from '../services/savedBuilds.service';

const AiUrlImport: React.FC = () => {
  const [url, setUrl] = useState<string>('');
  const [context, setContext] = useState<string>('WvW Zerg');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<UrlAnalysisResult | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

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
    setSaveMessage(null);

    const trimmedUrl = url.trim();
    if (!trimmedUrl) {
      setError("Veuillez entrer une URL de build valide.");
      return;
    }

    try {
      setLoading(true);
      const data = await aiService.analyzeUrl(trimmedUrl, context || 'WvW Zerg');
      setResult(data);
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Erreur lors de l'analyse de l'URL de build.";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!result) return;

    const { source, analysis } = result;

    setError(null);
    setSaveMessage(null);

    const defaultName = source.name?.trim() || 'Build importé depuis URL';
    const nameInput = window.prompt('Nom du build à sauvegarder :', defaultName);
    if (!nameInput || !nameInput.trim()) {
      return;
    }

    const name = nameInput.trim();

    const notesParts: string[] = [];
    if (source.url) {
      notesParts.push(`Source: ${source.url}`);
    }
    if (analysis?.summary) {
      notesParts.push(`Résumé IA: ${analysis.summary}`);
    }
    if (source.stats_text) {
      notesParts.push(`Stats détectées: ${source.stats_text}`);
    }
    if (source.runes_text) {
      notesParts.push(`Runes détectées: ${source.runes_text}`);
    }

    const notes = notesParts.length > 0 ? notesParts.join('\n\n') : undefined;

    try {
      setSaving(true);
      await savedBuildsService.create({
        name,
        chat_code: (source.chat_code as string | undefined) ?? undefined,
        game_mode: (analysis?.context as string | undefined) ?? context,
        synergy_score: (analysis?.synergy_score as string | undefined) ?? undefined,
        source_url: source.url,
        notes,
      });
      setSaveMessage('Build sauvegardé dans "Mes Builds".');
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Erreur lors de la sauvegarde du build.';
      setError(message);
    } finally {
      setSaving(false);
    }
  };

  const analysis = result?.analysis;
  const source = result?.source;

  const handleCopyChatCode = async () => {
    const chatCode = (source?.chat_code as string | undefined) ?? undefined;
    if (!chatCode) return;

    try {
      await navigator.clipboard.writeText(chatCode);
    } catch (err) {
      // Ignore clipboard errors silently
    }
  };

  const effectiveContext =
    (analysis?.context as string | undefined) || (source?.context as string | undefined) || context;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-white">Import de build par URL</h1>
          <p className="text-sm text-slate-400 mt-1">
            Collez une URL de build (Hardstuck, GuildJen, etc.) pour extraire le chat code, analyser la synergie et
            éventuellement sauvegarder le build.
          </p>
        </div>
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-4 space-y-4">
        <div className="grid gap-4 md:grid-cols-[minmax(0,3fr)_minmax(0,2fr)_auto] items-end">
          <div className="space-y-1">
            <label className="text-sm font-medium text-slate-200">URL du build</label>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-600"
              placeholder="https://hardstuck.gg/build/..."
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
          <button
            type="button"
            onClick={handleAnalyze}
            disabled={loading}
            className="inline-flex items-center justify-center rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {loading ? 'Analyse en cours…' : 'Importer & Analyser'}
          </button>
        </div>
        {error && <p className="text-sm text-red-400 mt-1">{error}</p>}
      </div>

      <div className="space-y-3">
        <h2 className="text-sm font-medium text-slate-200">Résultat</h2>
        {!result && !error && (
          <p className="text-sm text-slate-500">
            Aucun résultat pour le moment. Collez une URL de build puis lancez une analyse.
          </p>
        )}
        {result && (
          <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-4 space-y-4">
            {source && (
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3 mb-3">
                <div className="space-y-1">
                  <p className="text-xs uppercase tracking-wide text-slate-400">Source</p>
                  <div className="flex flex-col text-sm">
                    {source.name && <span className="font-semibold text-slate-50">{source.name}</span>}
                    <a
                      href={source.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-indigo-400 hover:text-indigo-300 hover:underline break-all"
                    >
                      {source.url}
                    </a>
                  </div>
                </div>
                <div className="space-y-1 text-right">
                  <p className="text-xs uppercase tracking-wide text-slate-400">Contexte</p>
                  <p className="text-sm font-semibold text-slate-50">{effectiveContext}</p>
                </div>
              </div>
            )}

            {source?.chat_code && (
              <div className="grid gap-3 md:grid-cols-[minmax(0,3fr)_auto] items-center">
                <div className="space-y-1">
                  <p className="text-xs uppercase tracking-wide text-slate-400">Chat Code (build)</p>
                  <code className="block rounded-md bg-slate-950 border border-slate-700 px-3 py-2 text-xs text-slate-100 break-all">
                    {source.chat_code}
                  </code>
                </div>
                <div className="flex flex-col gap-2 justify-center">
                  <button
                    type="button"
                    onClick={handleCopyChatCode}
                    className="inline-flex items-center justify-center rounded-md bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-100 hover:bg-slate-700"
                 >
                    Copier
                  </button>
                </div>
              </div>
            )}

            {analysis?.synergy_score && (
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="space-y-1">
                  <p className="text-xs uppercase tracking-wide text-slate-400">Score de synergie</p>
                  <span
                    className={`inline-flex items-center justify-center rounded-full px-4 py-2 text-lg font-semibold ${getScoreClasses(
                      analysis.synergy_score as string | undefined,
                    )}`}
                  >
                    {analysis.synergy_score}
                  </span>
                </div>
              </div>
            )}

            {(source?.stats_text || source?.runes_text) && (
              <div className="grid gap-4 md:grid-cols-2 mt-3">
                {source?.stats_text && (
                  <div>
                    <p className="text-xs uppercase tracking-wide text-slate-400 mb-1">Stats détectées</p>
                    <p className="text-sm text-slate-200 whitespace-pre-wrap">{source.stats_text}</p>
                  </div>
                )}
                {source?.runes_text && (
                  <div>
                    <p className="text-xs uppercase tracking-wide text-slate-400 mb-1">Runes détectées</p>
                    <p className="text-sm text-slate-200 whitespace-pre-wrap">{source.runes_text}</p>
                  </div>
                )}
              </div>
            )}

            {Array.isArray(analysis?.strengths) && analysis.strengths.length > 0 && (
              <div>
                <p className="text-xs uppercase tracking-wide text-slate-400 mb-1">Forces</p>
                <ul className="list-disc list-inside text-sm text-slate-200 space-y-1">
                  {analysis.strengths.map((s, idx) => (
                    <li key={idx}>{s}</li>
                  ))}
                </ul>
              </div>
            )}

            {Array.isArray(analysis?.weaknesses) && analysis.weaknesses.length > 0 && (
              <div>
                <p className="text-xs uppercase tracking-wide text-slate-400 mb-1">Faiblesses</p>
                <ul className="list-disc list-inside text-sm text-slate-200 space-y-1">
                  {analysis.weaknesses.map((w, idx) => (
                    <li key={idx}>{w}</li>
                  ))}
                </ul>
              </div>
            )}

            {analysis?.summary && (
              <div>
                <p className="text-xs uppercase tracking-wide text-slate-400 mb-1">Résumé</p>
                <p className="text-sm text-slate-200">{analysis.summary}</p>
              </div>
            )}

            <details className="mt-2">
              <summary className="text-xs text-slate-500 cursor-pointer">Voir le JSON brut</summary>
              <pre className="mt-2 max-h-64 overflow-auto rounded-md bg-slate-950 p-3 text-xs text-slate-300">
                {JSON.stringify(result, null, 2)}
              </pre>
            </details>

            <div className="mt-3 flex items-center justify-between gap-3">
              {saveMessage && <p className="text-xs text-emerald-400">{saveMessage}</p>}
              <button
                type="button"
                onClick={handleSave}
                disabled={saving || !analysis}
                className="inline-flex items-center justify-center rounded-md bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-emerald-500 disabled:opacity-60 disabled:cursor-not-allowed"
              >
                {saving ? 'Sauvegarde…' : 'Sauvegarder ce build'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AiUrlImport;
