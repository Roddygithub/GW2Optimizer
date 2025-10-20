import React from 'react';
import { Sword, Shield, Heart, Star, Eye, Trash2 } from 'lucide-react';

interface BuildCardProps {
  build: {
    id: string;
    name: string;
    profession: string;
    role: string;
    game_mode: string;
    description?: string;
    rating?: number;
    is_public?: boolean;
  };
  onView?: (id: string) => void;
  onDelete?: (id: string) => void;
  showActions?: boolean;
}

export const BuildCard: React.FC<BuildCardProps> = ({ 
  build, 
  onView, 
  onDelete,
  showActions = true 
}) => {
  const getProfessionColor = (profession: string) => {
    const colors: Record<string, string> = {
      Guardian: 'from-blue-500 to-cyan-400',
      Warrior: 'from-yellow-600 to-orange-500',
      Revenant: 'from-red-600 to-pink-500',
      Engineer: 'from-amber-600 to-yellow-500',
      Ranger: 'from-green-600 to-emerald-500',
      Thief: 'from-gray-700 to-gray-500',
      Elementalist: 'from-red-500 to-purple-500',
      Mesmer: 'from-purple-600 to-pink-500',
      Necromancer: 'from-green-800 to-teal-700',
    };
    return colors[profession] || 'from-gray-600 to-gray-400';
  };

  const getRoleIcon = (role: string) => {
    switch (role.toLowerCase()) {
      case 'dps':
        return <Sword size={16} className="text-red-400" />;
      case 'tank':
        return <Shield size={16} className="text-blue-400" />;
      case 'support':
      case 'healer':
        return <Heart size={16} className="text-green-400" />;
      default:
        return <Star size={16} className="text-yellow-400" />;
    }
  };

  return (
    <div className="bg-gray-800 rounded-lg overflow-hidden border border-gray-700 hover:border-cyan-500 transition-all duration-300 hover:shadow-lg hover:shadow-cyan-500/20">
      {/* Header with profession gradient */}
      <div className={`bg-gradient-to-r ${getProfessionColor(build.profession)} p-4`}>
        <div className="flex items-start justify-between">
          <div>
            <h3 className="text-xl font-bold text-white mb-1">{build.name}</h3>
            <div className="flex items-center gap-2 text-white/90 text-sm">
              <span className="font-semibold">{build.profession}</span>
              <span>•</span>
              <div className="flex items-center gap-1">
                {getRoleIcon(build.role)}
                <span>{build.role}</span>
              </div>
            </div>
          </div>
          {build.rating && (
            <div className="bg-white/20 backdrop-blur-sm px-3 py-1 rounded-full flex items-center gap-1">
              <Star size={14} className="text-yellow-300 fill-yellow-300" />
              <span className="text-white font-semibold text-sm">{build.rating.toFixed(1)}</span>
            </div>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        <div className="flex items-center gap-2 mb-3">
          <span className="bg-gray-700 text-gray-300 px-2 py-1 rounded text-xs font-medium">
            {build.game_mode}
          </span>
          {build.is_public && (
            <span className="bg-cyan-900/30 text-cyan-400 px-2 py-1 rounded text-xs font-medium border border-cyan-700">
              Public
            </span>
          )}
        </div>

        {build.description && (
          <p className="text-gray-400 text-sm line-clamp-2 mb-4">
            {build.description}
          </p>
        )}

        {/* Actions */}
        {showActions && (
          <div className="flex gap-2">
            {onView && (
              <button
                onClick={() => onView(build.id)}
                className="flex-1 bg-cyan-600 hover:bg-cyan-700 text-white py-2 px-4 rounded-lg flex items-center justify-center gap-2 transition-colors"
              >
                <Eye size={16} />
                View
              </button>
            )}
            {onDelete && (
              <button
                onClick={() => onDelete(build.id)}
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
