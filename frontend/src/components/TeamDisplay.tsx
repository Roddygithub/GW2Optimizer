import { Shield, Heart, Zap, Swords, Target, Award, TrendingUp, Activity, type LucideIcon } from 'lucide-react';

interface TeamDisplayProps {
  data: {
    team_size: number;
    groups: Array<{
      index: number;
      slots: Array<{
        role: string;
        profession: string;
        specialization: string;
        gear_mix?: Record<string, string>;
        equipment: {
          stats: string;
          rune: string;
          sigils: string[];
          relic?: string | null;
          example_armor?: Array<{
            slot: string;
            id: number;
            name: string;
            stats?: string | null;
          }>;
        };
        performance: {
          burst_damage: number;
          survivability: number;
          dps_increase: number;
        };
        advisor_reason?: string;
        advisor_alternatives?: {
          prefix: string;
          rune: string;
          sigils: string[];
          total_damage: number;
          survivability: number;
          overall_score: number;
        }[];
      }>;
    }>;
    synergy: {
      score: string;
      details: {
        stability?: string;
        healing?: string;
        boon_share?: string;
        boon_strip?: string;
        damage?: string;
        cleanse?: string;
      };
    };
    notes: string[];
  };
}

// Icônes de classes GW2
const classIcons: Record<string, string> = {
  Guardian: '🛡️',
  Warrior: '⚔️',
  Revenant: '🌊',
  Engineer: '🔧',
  Ranger: '🏹',
  Thief: '🗡️',
  Elementalist: '🔥',
  Mesmer: '✨',
  Necromancer: '💀',
};

// Couleurs par rôle
const roleColors: Record<string, { bg: string; text: string; icon: LucideIcon }> = {
  stab: { bg: 'bg-blue-500/20', text: 'text-blue-400', icon: Shield },
  heal: { bg: 'bg-green-500/20', text: 'text-green-400', icon: Heart },
  boon: { bg: 'bg-yellow-500/20', text: 'text-yellow-400', icon: Zap },
  strip: { bg: 'bg-red-500/20', text: 'text-red-400', icon: Target },
  dps: { bg: 'bg-red-500/20', text: 'text-red-400', icon: Swords },
  tank: { bg: 'bg-cyan-500/20', text: 'text-cyan-400', icon: Shield },
  support: { bg: 'bg-purple-500/20', text: 'text-purple-400', icon: Heart },
  cleanse: { bg: 'bg-emerald-500/20', text: 'text-emerald-400', icon: Activity },
};

// Badge de synergie
const SynergyBadge = ({ score }: { score: string }) => {
  const colors: Record<string, string> = {
    S: 'bg-gradient-to-r from-yellow-500 to-orange-500',
    A: 'bg-gradient-to-r from-green-500 to-emerald-500',
    B: 'bg-gradient-to-r from-blue-500 to-cyan-500',
    C: 'bg-gradient-to-r from-gray-500 to-slate-500',
  };

  return (
    <div className={`${colors[score] || colors.C} px-4 py-2 rounded-full inline-flex items-center gap-2`}>
      <Award className="w-5 h-5 text-white" />
      <span className="text-white font-bold text-lg">Synergie {score}</span>
    </div>
  );
};

// Mini graphique de performance
const PerformanceBar = ({ value, max, color }: { value: number; max: number; color: string }) => {
  const percentage = Math.min((value / max) * 100, 100);
  return (
    <div className="w-full bg-slate-700 rounded-full h-2">
      <div
        className={`h-2 rounded-full transition-all ${color}`}
        style={{ width: `${percentage}%` }}
      />
    </div>
  );
};

export default function TeamDisplay({ data }: TeamDisplayProps) {
  return (
    <div className="mt-6 space-y-6">
      {/* Header avec synergie */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-xl font-bold text-white mb-1">
            Équipe de {data.team_size} joueurs
          </h3>
          <p className="text-sm text-gray-400">{data.groups.length} groupes</p>
        </div>
        <SynergyBadge score={data.synergy.score} />
      </div>

      {/* Détails de synergie */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {Object.entries(data.synergy.details).map(([key, value]) => {
          const icons: Record<string, LucideIcon> = {
            stability: Shield,
            healing: Heart,
            boon_share: Zap,
            boon_strip: Target,
            damage: Swords,
            cleanse: Activity,
          };
          const Icon = icons[key] || Award;
          const colorMap: Record<string, string> = {
            Excellent: 'text-green-400',
            Perfect: 'text-green-400',
            Optimal: 'text-green-400',
            'Very High': 'text-green-400',
            Good: 'text-blue-400',
            Effective: 'text-blue-400',
            High: 'text-blue-400',
            Moderate: 'text-yellow-400',
            Weak: 'text-red-400',
          };
          const color = colorMap[value as string] || 'text-gray-400';

          return (
            <div key={key} className="bg-slate-800/50 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-1">
                <Icon className={`w-4 h-4 ${color}`} />
                <span className="text-xs text-gray-400 capitalize">{key.replace('_', ' ')}</span>
              </div>
              <span className={`text-sm font-medium ${color}`}>{value}</span>
            </div>
          );
        })}
      </div>

      {/* Groupes */}
      {data.groups.map((group) => (
        <div key={group.index} className="space-y-3">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-8 h-8 bg-purple-500/20 rounded-full flex items-center justify-center">
              <span className="text-sm font-bold text-purple-400">{group.index}</span>
            </div>
            <h4 className="text-lg font-semibold text-white">Groupe {group.index}</h4>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {group.slots.map((slot, idx) => {
              const roleConfig = roleColors[slot.role] || roleColors.dps;
              const RoleIcon = roleConfig.icon;
              const classIcon = classIcons[slot.profession] || '⚡';

              return (
                <div
                  key={idx}
                  className="bg-slate-800/70 border border-purple-500/20 rounded-lg p-4 hover:border-purple-500/40 transition-all"
                >
                  {/* Header */}
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <span className="text-2xl">{classIcon}</span>
                      <div>
                        <h5 className="text-white font-medium text-sm">
                          {slot.profession}
                        </h5>
                        <p className="text-xs text-gray-400">{slot.specialization}</p>
                      </div>
                    </div>
                    <div className={`${roleConfig.bg} px-2 py-1 rounded flex items-center gap-1`}>
                      <RoleIcon className={`w-3 h-3 ${roleConfig.text}`} />
                      <span className={`text-xs font-medium ${roleConfig.text} capitalize`}>
                        {slot.role}
                      </span>
                    </div>
                  </div>

                  {/* Equipment */}
                  <div className="space-y-2 mb-3">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-gray-400">Stats</span>
                      <span className="text-purple-400 font-medium">{slot.equipment.stats}</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-gray-400">Rune</span>
                      <span
                        className="text-blue-400 font-medium"
                        title="Rune recommandée pour ce build (issue de l'analyse)"
                      >
                        {slot.equipment.rune}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-gray-400">Sigils</span>
                      <span className="text-green-400 font-medium">
                        {slot.equipment.sigils.join(', ')}
                      </span>
                    </div>
                    {slot.equipment.relic && (
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-400">Relique</span>
                        <span
                          className="text-amber-400 font-medium"
                          title="Relique recommandée pour ce build (issue de l'analyse)"
                        >
                          {slot.equipment.relic}
                        </span>
                      </div>
                    )}
                    {/* Mix d'armure détaillé issu du greedy solver, si disponible */}
                    {slot.gear_mix && Object.keys(slot.gear_mix).length > 0 && (
                      <div className="pt-2 border-t border-slate-700 mt-1 space-y-1">
                        <div className="flex items-center justify-between text-[11px] text-gray-400">
                          <span>Mix d'armure (préfixes)</span>
                        </div>
                        <div className="space-y-0.5">
                          {Object.entries(slot.gear_mix).map(([armorSlot, prefix]) => (
                            <div
                              key={armorSlot}
                              className="flex items-center justify-between text-[11px] text-gray-300"
                            >
                              <span className="text-gray-500">{armorSlot}</span>
                              <span className="text-right text-purple-300">{prefix}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {Array.isArray(slot.equipment.example_armor) &&
                      slot.equipment.example_armor.length > 0 && (
                        <div className="pt-2 border-t border-slate-700 mt-1 space-y-1">
                          <div className="flex items-center justify-between text-[11px] text-gray-400">
                            <span>Exemple d'armure</span>
                          </div>
                          <div className="space-y-0.5">
                            {slot.equipment.example_armor.map((piece) => (
                              <div
                                key={`${piece.slot}-${piece.id}`}
                                className="flex items-center justify-between text-[11px] text-gray-300"
                              >
                                <span className="text-gray-500">{piece.slot}</span>
                                <span className="text-right">
                                  {piece.name}
                                  {piece.stats && <span className="text-gray-500"> · {piece.stats}</span>}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                  </div>

                  {/* Performance */}
                  <div className="space-y-2 pt-3 border-t border-slate-700">
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs text-gray-400">Burst</span>
                        <span className="text-xs text-orange-400 font-medium">
                          {Math.round(slot.performance.burst_damage).toLocaleString()}
                        </span>
                      </div>
                      <PerformanceBar
                        value={slot.performance.burst_damage}
                        max={40000}
                        color="bg-orange-500"
                      />
                    </div>
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs text-gray-400">Survie</span>
                        <span className="text-xs text-cyan-400 font-medium">
                          {slot.performance.survivability.toFixed(1)}
                        </span>
                      </div>
                      <PerformanceBar
                        value={slot.performance.survivability}
                        max={5}
                        color="bg-cyan-500"
                      />
                    </div>
                  </div>

                  {slot.advisor_reason && (
                    <p className="mt-2 text-[11px] text-gray-400 italic">
                      {slot.advisor_reason}
                    </p>
                  )}

                  {slot.advisor_alternatives && slot.advisor_alternatives.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-slate-800">
                      <p className="text-[11px] text-gray-500 mb-1">Autres presets testés :</p>
                      <div className="flex flex-wrap gap-1">
                        {slot.advisor_alternatives.map((alt, idx) => (
                          <span
                            key={`${alt.prefix}-${idx}`}
                            className="inline-flex items-center rounded-full bg-slate-900 px-2 py-0.5 text-[10px] text-gray-300 border border-purple-500/30"
                          >
                            {alt.prefix} · {alt.rune}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ))}

      {/* Notes */}
      {data.notes.length > 0 && (
        <div className="bg-slate-800/50 border border-purple-500/20 rounded-lg p-4">
          <h4 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-purple-400" />
            Recommandations
          </h4>
          <ul className="space-y-2">
            {data.notes.map((note, idx) => (
              <li key={idx} className="text-sm text-gray-300 flex items-start gap-2">
                <span className="text-purple-400 mt-0.5">•</span>
                <span>{note}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
