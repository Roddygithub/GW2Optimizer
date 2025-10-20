import React from 'react';
import { Users, Eye, Trash2, Shield, Zap } from 'lucide-react';

interface TeamCardProps {
  team: {
    id: string;
    name: string;
    game_mode: string;
    description?: string;
    slots: Array<{
      profession: string;
      role?: string;
      player_name?: string;
    }>;
    synergy_score?: number;
    is_public?: boolean;
  };
  onView?: (id: string) => void;
  onDelete?: (id: string) => void;
  showActions?: boolean;
}

export const TeamCard: React.FC<TeamCardProps> = ({ 
  team, 
  onView, 
  onDelete,
  showActions = true 
}) => {
  const getProfessionColor = (profession: string) => {
    const colors: Record<string, string> = {
      Guardian: 'bg-blue-500',
      Warrior: 'bg-yellow-600',
      Revenant: 'bg-red-600',
      Engineer: 'bg-amber-600',
      Ranger: 'bg-green-600',
      Thief: 'bg-gray-700',
      Elementalist: 'bg-purple-600',
      Mesmer: 'bg-pink-600',
      Necromancer: 'bg-teal-700',
    };
    return colors[profession] || 'bg-gray-600';
  };

  const getSynergyColor = (score?: number) => {
    if (!score) return 'text-gray-400';
    if (score >= 80) return 'text-green-400';
    if (score >= 60) return 'text-yellow-400';
    return 'text-orange-400';
  };

  return (
    <div className="bg-gray-800 rounded-lg overflow-hidden border border-gray-700 hover:border-cyan-500 transition-all duration-300 hover:shadow-lg hover:shadow-cyan-500/20">
      {/* Header */}
      <div className="bg-gradient-to-r from-cyan-600 to-blue-600 p-4">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="text-xl font-bold text-white mb-1">{team.name}</h3>
            <div className="flex items-center gap-2 text-white/90 text-sm">
              <Users size={16} />
              <span>{team.slots.length} members</span>
              <span>•</span>
              <span>{team.game_mode}</span>
            </div>
          </div>
          {team.synergy_score !== undefined && (
            <div className="bg-white/20 backdrop-blur-sm px-3 py-1 rounded-full flex items-center gap-1">
              <Zap size={14} className={getSynergyColor(team.synergy_score)} />
              <span className={`font-semibold text-sm ${getSynergyColor(team.synergy_score)}`}>
                {team.synergy_score}%
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {/* Team Members */}
        <div className="mb-4">
          <div className="flex flex-wrap gap-2">
            {team.slots.map((slot, index) => (
              <div
                key={index}
                className={`${getProfessionColor(slot.profession)} px-3 py-1 rounded-full text-white text-sm font-medium flex items-center gap-1`}
                title={slot.player_name || slot.profession}
              >
                {slot.profession.substring(0, 3)}
                {slot.role && (
                  <span className="text-xs opacity-75">
                    ({slot.role})
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>

        {team.description && (
          <p className="text-gray-400 text-sm line-clamp-2 mb-4">
            {team.description}
          </p>
        )}

        <div className="flex items-center gap-2 mb-4">
          {team.is_public && (
            <span className="bg-cyan-900/30 text-cyan-400 px-2 py-1 rounded text-xs font-medium border border-cyan-700">
              Public
            </span>
          )}
        </div>

        {/* Actions */}
        {showActions && (
          <div className="flex gap-2">
            {onView && (
              <button
                onClick={() => onView(team.id)}
                className="flex-1 bg-cyan-600 hover:bg-cyan-700 text-white py-2 px-4 rounded-lg flex items-center justify-center gap-2 transition-colors"
              >
                <Eye size={16} />
                View
              </button>
            )}
            {onDelete && (
              <button
                onClick={() => onDelete(team.id)}
                className="bg-red-600 hover:bg-red-700 text-white py-2 px-4 rounded-lg flex items-center justify-center gap-2 transition-colors"
              >
                <Trash2 size={16} />
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
