import React, { useState } from 'react';
import { aiService, BuildAnalysisResult } from '../services/ai.service';
import { savedBuildsService } from '../services/savedBuilds.service';

const AiBuildLab: React.FC = () => {
  const [specId, setSpecId] = useState<string>('');
  const [traitIds, setTraitIds] = useState<string>('');
  const [skillIds, setSkillIds] = useState<string>('');
  const [context, setContext] = useState<string>('WvW Zerg');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<BuildAnalysisResult | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

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

  const handleCopyChatCode = async () => {
    if (!result?.chat_code) return;

    try {
      await navigator.clipboard.writeText(result.chat_code);
    } catch (err) {
      // Fallback minimal en cas d'échec de l'API clipboard
      // eslint-disable-next-line no-alert
      window.alert('Impossible de copier le chat code automatiquement. Copiez-le manuellement.');
    }
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

  const getRoleBadgeClasses = (role?: string): string => {
    if (!role) {
      return 'bg-slate-700 text-slate-200 border border-slate-500/30';
    }
    const normalized = role.toLowerCase();
    if (normalized.includes('heal')) {
      return 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40';
    }
    if (normalized.includes('dps')) {
      return 'bg-red-500/20 text-red-300 border border-red-500/40';
    }
    return 'bg-slate-700 text-slate-200 border border-slate-500/30';
  };

  const handleAnalyze = async () => {
    setError(null);
    setResult(null);
    setSaveMessage(null);

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

  const handleSave = async () => {
    if (!result) return;

    setError(null);
    setSaveMessage(null);

    const defaultName = 'Build analysé';
    const nameInput = window.prompt('Nom du build à sauvegarder :', defaultName);
    if (!nameInput || !nameInput.trim()) {
      return;
    }

    const name = nameInput.trim();

    try {
      setSaving(true);
      await savedBuildsService.create({
        name,
        game_mode: (result.context as string | undefined) ?? context,
        synergy_score: result.synergy_score as string | undefined,
        notes: (result.summary as string | undefined) ?? undefined,
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

            {result.gear_optimization && (
              <div className="pt-3 border-t border-slate-800 space-y-3">
                <div className="flex items-center justify-between gap-3">
                  <div className="space-y-1">
                    <p className="text-xs uppercase tracking-wide text-slate-400">Recommandation d'équipement</p>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-slate-500">Rôle optimisé&nbsp;:</span>
                      <span
                        className={`inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium ${getRoleBadgeClasses(
                          result.gear_optimization.role,
                        )}`}
                      >
                        {result.gear_optimization.role}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500">
                      Mode&nbsp;: {result.gear_optimization.mode} · Niveau&nbsp;:{' '}
                      {result.gear_optimization.experience}
                    </p>
                  </div>
                </div>

                <div className="grid gap-3 md:grid-cols-2">
                  <div className="space-y-2">
                    <p className="text-xs uppercase tracking-wide text-slate-400">Preset choisi</p>
                    <div className="rounded-md border border-slate-700 bg-slate-900 p-3 space-y-2 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="text-slate-400">Stats</span>
                        <span className="text-indigo-400 font-medium">
                          {result.gear_optimization.chosen.prefix}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-slate-400">Rune</span>
                        <span
                          className="text-blue-400 font-medium"
                          title="Rune recommandée pour ce build (issue de l'analyse)"
                        >
                          {result.gear_optimization.chosen.rune}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-slate-400">Sigils</span>
                        <span className="text-emerald-400 font-medium">
                          {result.gear_optimization.chosen.sigils.join(', ')}
                        </span>
                      </div>
                      {result.gear_optimization.chosen.relic && (
                        <div className="flex items-center justify-between">
                          <span className="text-slate-400">Relique</span>
                          <span className="text-amber-400 font-medium">
                            {result.gear_optimization.chosen.relic}
                          </span>
                        </div>
                      )}
                      {(typeof result.gear_optimization.chosen.rotation_hps_10s === 'number' ||
                        typeof result.gear_optimization.chosen.rotation_dps_10s === 'number') && (
                        <div className="pt-1 mt-1 border-t border-slate-700/60 space-y-1">
                          {typeof result.gear_optimization.chosen.rotation_dps_10s === 'number' && (
                            <div className="flex items-center justify-between">
                              <span className="text-slate-400">DPS rotation (10s)</span>
                              <span className="text-slate-100 font-medium">
                                {Math.round(result.gear_optimization.chosen.rotation_dps_10s)}
                              </span>
                            </div>
                          )}
                          {typeof result.gear_optimization.chosen.rotation_hps_10s === 'number' && (
                            <div className="flex items-center justify-between">
                              <span className="text-slate-400">HPS estimé (rotation 10s)</span>
                              <span className="text-emerald-300 font-semibold">
                                {Math.round(result.gear_optimization.chosen.rotation_hps_10s)}
                              </span>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <p className="text-xs uppercase tracking-wide text-slate-400">Autres presets testés</p>
                    <div className="flex flex-wrap gap-1">
                      {(result.gear_optimization.alternatives ?? []).map((alt, idx) => (
                        <span
                          key={`${alt.prefix}-${idx}`}
                          className="inline-flex items-center rounded-full bg-slate-900 px-2 py-0.5 text-[10px] text-gray-300 border border-indigo-500/30"
                        >
                          {alt.prefix} · {alt.rune}
                        </span>
                      ))}
                      {(!result.gear_optimization.alternatives ||
                        result.gear_optimization.alternatives.length === 0) && (
                        <span className="text-[11px] text-slate-500">Aucune alternative significative.</span>
                      )}
                    </div>
                  </div>
                </div>

                {Array.isArray(result.gear_optimization.chosen.example_armor) &&
                  result.gear_optimization.chosen.example_armor.length > 0 && (
                    <div className="grid gap-3 md:grid-cols-2">
                      <div className="space-y-2">
                        <p className="text-xs uppercase tracking-wide text-slate-400">Exemple d'armure</p>
                        <div className="rounded-md border border-slate-700 bg-slate-900 p-3 space-y-1 text-xs">
                          {result.gear_optimization.chosen.example_armor.map((piece) => (
                            <div
                              key={`${piece.slot}-${piece.id}`}
                              className="flex items-center justify-between gap-2"
                            >
                              <span className="text-slate-400">{piece.slot}</span>
                              <span className="text-slate-200 text-right">
                                {piece.name}
                                {piece.stats && (
                                  <span className="text-slate-500"> · {piece.stats}</span>
                                )}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>

                      {result.chat_code && (
                        <div className="space-y-2">
                          <p className="text-xs uppercase tracking-wide text-slate-400">Export (Chat Code)</p>
                          <div className="rounded-md border border-slate-700 bg-slate-900 p-3 flex items-center justify-between gap-2">
                            <code className="text-[11px] text-slate-100 break-all">
                              {result.chat_code}
                            </code>
                            <button
                              type="button"
                              onClick={handleCopyChatCode}
                              className="inline-flex items-center justify-center rounded-md bg-slate-800 px-2 py-1 text-[11px] font-medium text-slate-100 hover:bg-slate-700"
                            >
                              Copier
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                {result.gear_optimization.chosen.reason && (
                  <p className="text-[11px] text-slate-500 italic">
                    {result.gear_optimization.chosen.reason}
                  </p>
                )}
              </div>
            )}

            {/* Meta Comparison Section */}
            {result.meta_comparison?.closest_meta && (
              <div className="rounded-lg border border-purple-500/30 bg-purple-950/20 p-4 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-purple-300">🎯 Comparaison avec la Méta</h3>
                  <span
                    className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                      (result.meta_comparison.similarity_score ?? 0) >= 0.9
                        ? 'bg-emerald-500/30 text-emerald-300'
                        : (result.meta_comparison.similarity_score ?? 0) >= 0.7
                          ? 'bg-amber-500/30 text-amber-300'
                          : 'bg-red-500/30 text-red-300'
                    }`}
                  >
                    {Math.round((result.meta_comparison.similarity_score ?? 0) * 100)}% similaire
                  </span>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-400">Build méta le plus proche</span>
                    <span className="text-purple-300 font-medium">
                      {result.meta_comparison.closest_meta.name}
                    </span>
                  </div>

                  {/* Similarity Progress Bar */}
                  <div className="w-full bg-slate-800 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all ${
                        (result.meta_comparison.similarity_score ?? 0) >= 0.9
                          ? 'bg-emerald-500'
                          : (result.meta_comparison.similarity_score ?? 0) >= 0.7
                            ? 'bg-amber-500'
                            : 'bg-red-500'
                      }`}
                      style={{ width: `${(result.meta_comparison.similarity_score ?? 0) * 100}%` }}
                    />
                  </div>

                  <div className="grid gap-2 md:grid-cols-2 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="text-slate-500">Source</span>
                      <span className="text-slate-300">
                        {result.meta_comparison.closest_meta.source ?? 'Community'}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-slate-500">Stats recommandées</span>
                      <span className="text-indigo-400">
                        {result.meta_comparison.closest_meta.stats_text ?? 'N/A'}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-slate-500">Rune recommandée</span>
                      <span className="text-blue-400">
                        {result.meta_comparison.closest_meta.runes_text ?? 'N/A'}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-slate-500">Rôle détecté</span>
                      <span className="text-slate-300">
                        {result.meta_comparison.user_role ?? 'N/A'}
                        {result.meta_comparison.role_confidence && (
                          <span className="text-slate-500 text-[10px] ml-1">
                            ({Math.round(result.meta_comparison.role_confidence * 100)}%)
                          </span>
                        )}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Equipment Comparison */}
                {result.meta_comparison.equipment_comparison && (
                  <div className="pt-2 border-t border-purple-500/20 space-y-2">
                    <p className="text-xs text-slate-400">Comparaison équipement</p>
                    <div className="grid gap-2 md:grid-cols-2 text-xs">
                      <div className="flex items-center gap-2">
                        <span
                          className={`w-2 h-2 rounded-full ${
                            result.meta_comparison.equipment_comparison.stats_match
                              ? 'bg-emerald-500'
                              : 'bg-amber-500'
                          }`}
                        />
                        <span className="text-slate-400">Stats:</span>
                        <span
                          className={
                            result.meta_comparison.equipment_comparison.stats_match
                              ? 'text-emerald-400'
                              : 'text-amber-400'
                          }
                        >
                          {result.meta_comparison.equipment_comparison.user_stats ?? 'N/A'}
                          {!result.meta_comparison.equipment_comparison.stats_match &&
                            result.meta_comparison.equipment_comparison.meta_stats && (
                              <span className="text-slate-500">
                                {' '}
                                → {result.meta_comparison.equipment_comparison.meta_stats}
                              </span>
                            )}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span
                          className={`w-2 h-2 rounded-full ${
                            result.meta_comparison.equipment_comparison.rune_match
                              ? 'bg-emerald-500'
                              : 'bg-amber-500'
                          }`}
                        />
                        <span className="text-slate-400">Rune:</span>
                        <span
                          className={
                            result.meta_comparison.equipment_comparison.rune_match
                              ? 'text-emerald-400'
                              : 'text-amber-400'
                          }
                        >
                          {result.meta_comparison.equipment_comparison.user_rune ?? 'N/A'}
                          {!result.meta_comparison.equipment_comparison.rune_match &&
                            result.meta_comparison.equipment_comparison.meta_rune && (
                              <span className="text-slate-500">
                                {' '}
                                → {result.meta_comparison.equipment_comparison.meta_rune}
                              </span>
                            )}
                        </span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Recommendations */}
                {result.meta_comparison.recommendations &&
                  result.meta_comparison.recommendations.length > 0 && (
                    <div className="pt-2 border-t border-purple-500/20 space-y-2">
                      <p className="text-xs text-slate-400">💡 Recommandations</p>
                      <ul className="space-y-1">
                        {result.meta_comparison.recommendations.map((rec, idx) => (
                          <li key={idx} className="text-xs text-slate-300 pl-3 relative">
                            <span className="absolute left-0 text-purple-400">•</span>
                            {rec}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                {/* Meta build notes */}
                {result.meta_comparison.closest_meta.notes && (
                  <p className="text-[11px] text-slate-500 italic">
                    ℹ️ {result.meta_comparison.closest_meta.notes}
                  </p>
                )}
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
                disabled={saving}
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

export default AiBuildLab;
