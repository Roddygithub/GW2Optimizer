import React from 'react';
import { Shield, Sword, Heart, Zap } from 'lucide-react';

interface BuildVisualizationProps {
  build: {
    name: string;
    profession: string;
    role: string;
    traits?: Record<string, any>;
    skills?: string[];
    equipment?: Record<string, any>;
    stats?: {
      power?: number;
      precision?: number;
      toughness?: number;
      vitality?: number;
    };
  };
}

export const BuildVisualization: React.FC<BuildVisualizationProps> = ({ build }) => {
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

  return (
    <div className="bg-gray-900 rounded-lg p-6 border border-gray-700">
      {/* Header */}
      <div className={`bg-gradient-to-r ${getProfessionColor(build.profession)} p-4 rounded-t-lg -mx-6 -mt-6 mb-6`}>
        <h2 className="text-2xl font-bold text-white">{build.name}</h2>
        <div className="flex gap-4 mt-2 text-white/90">
          <span className="font-semibold">{build.profession}</span>
          <span>•</span>
          <span>{build.role}</span>
        </div>
      </div>

      {/* Stats */}
      {build.stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          {build.stats.power && (
            <div className="bg-gray-800 p-3 rounded-lg flex items-center gap-3">
              <Sword className="text-red-400" size={24} />
              <div>
                <div className="text-xs text-gray-400">Power</div>
                <div className="text-lg font-bold text-white">{build.stats.power}</div>
              </div>
            </div>
          )}
          {build.stats.precision && (
            <div className="bg-gray-800 p-3 rounded-lg flex items-center gap-3">
              <Zap className="text-yellow-400" size={24} />
              <div>
                <div className="text-xs text-gray-400">Precision</div>
                <div className="text-lg font-bold text-white">{build.stats.precision}</div>
              </div>
            </div>
          )}
          {build.stats.toughness && (
            <div className="bg-gray-800 p-3 rounded-lg flex items-center gap-3">
              <Shield className="text-blue-400" size={24} />
              <div>
                <div className="text-xs text-gray-400">Toughness</div>
                <div className="text-lg font-bold text-white">{build.stats.toughness}</div>
              </div>
            </div>
          )}
          {build.stats.vitality && (
            <div className="bg-gray-800 p-3 rounded-lg flex items-center gap-3">
              <Heart className="text-green-400" size={24} />
              <div>
                <div className="text-xs text-gray-400">Vitality</div>
                <div className="text-lg font-bold text-white">{build.stats.vitality}</div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Skills */}
      {build.skills && build.skills.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-white mb-3">Skills</h3>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
            {build.skills.map((skill, index) => (
              <div
                key={index}
                className="bg-gray-800 p-2 rounded text-center text-sm text-gray-300 hover:bg-gray-700 transition-colors"
              >
                {skill}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Equipment */}
      {build.equipment && (
        <div>
          <h3 className="text-lg font-semibold text-white mb-3">Equipment</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {Object.entries(build.equipment).map(([slot, item]) => (
              <div key={slot} className="bg-gray-800 p-3 rounded-lg">
                <div className="text-xs text-gray-400 uppercase">{slot}</div>
                <div className="text-white font-medium">{String(item)}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
