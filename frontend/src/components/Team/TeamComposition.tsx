import React, { useState } from 'react';
import { Users, Plus, X, AlertCircle } from 'lucide-react';

interface TeamMember {
  id: string;
  profession: string;
  role: string;
  playerName?: string;
}

interface TeamCompositionProps {
  onAnalyze?: (team: TeamMember[]) => void;
  maxSize?: number;
}

const PROFESSIONS = [
  'Guardian', 'Revenant', 'Warrior', 'Engineer', 'Ranger',
  'Thief', 'Elementalist', 'Mesmer', 'Necromancer'
];

const ROLES = ['DPS', 'Support', 'Tank', 'Hybrid', 'Healer', 'Boon'];

export const TeamComposition: React.FC<TeamCompositionProps> = ({ 
  onAnalyze, 
  maxSize = 10 
}) => {
  const [team, setTeam] = useState<TeamMember[]>([]);
  const [isAdding, setIsAdding] = useState(false);
  const [newMember, setNewMember] = useState({
    profession: PROFESSIONS[0],
    role: ROLES[0],
    playerName: ''
  });

  const addMember = () => {
    if (team.length >= maxSize) {
      alert(`Maximum team size is ${maxSize}`);
      return;
    }

    const member: TeamMember = {
      id: Date.now().toString(),
      profession: newMember.profession,
      role: newMember.role,
      playerName: newMember.playerName || undefined
    };

    setTeam([...team, member]);
    setNewMember({ profession: PROFESSIONS[0], role: ROLES[0], playerName: '' });
    setIsAdding(false);
  };

  const removeMember = (id: string) => {
    setTeam(team.filter(m => m.id !== id));
  };

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

  return (
    <div className="bg-gray-900 rounded-lg p-6 border border-gray-700">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Users className="text-cyan-400" size={28} />
          <div>
            <h2 className="text-2xl font-bold text-white">Team Composition</h2>
            <p className="text-gray-400 text-sm">{team.length}/{maxSize} members</p>
          </div>
        </div>
        <button
          onClick={() => setIsAdding(!isAdding)}
          className="bg-cyan-600 hover:bg-cyan-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
          disabled={team.length >= maxSize}
        >
          <Plus size={20} />
          Add Member
        </button>
      </div>

      {/* Add Member Form */}
      {isAdding && (
        <div className="bg-gray-800 p-4 rounded-lg mb-4 border border-gray-700">
          <h3 className="text-white font-semibold mb-3">New Team Member</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-3">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Profession</label>
              <select
                value={newMember.profession}
                onChange={(e) => setNewMember({ ...newMember, profession: e.target.value })}
                className="w-full bg-gray-700 text-white rounded px-3 py-2 border border-gray-600 focus:border-cyan-500 focus:outline-none"
              >
                {PROFESSIONS.map(prof => (
                  <option key={prof} value={prof}>{prof}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Role</label>
              <select
                value={newMember.role}
                onChange={(e) => setNewMember({ ...newMember, role: e.target.value })}
                className="w-full bg-gray-700 text-white rounded px-3 py-2 border border-gray-600 focus:border-cyan-500 focus:outline-none"
              >
                {ROLES.map(role => (
                  <option key={role} value={role}>{role}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Player Name (Optional)</label>
              <input
                type="text"
                value={newMember.playerName}
                onChange={(e) => setNewMember({ ...newMember, playerName: e.target.value })}
                placeholder="Player name"
                className="w-full bg-gray-700 text-white rounded px-3 py-2 border border-gray-600 focus:border-cyan-500 focus:outline-none"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={addMember}
              className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded transition-colors"
            >
              Add
            </button>
            <button
              onClick={() => setIsAdding(false)}
              className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Team Members List */}
      {team.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <AlertCircle size={48} className="mx-auto mb-3 opacity-50" />
          <p>No team members yet. Click "Add Member" to start building your team.</p>
        </div>
      ) : (
        <div className="space-y-2 mb-4">
          {team.map((member) => (
            <div
              key={member.id}
              className="bg-gray-800 p-4 rounded-lg flex items-center justify-between hover:bg-gray-750 transition-colors"
            >
              <div className="flex items-center gap-4">
                <div className={`${getProfessionColor(member.profession)} w-12 h-12 rounded-lg flex items-center justify-center text-white font-bold`}>
                  {member.profession.substring(0, 2).toUpperCase()}
                </div>
                <div>
                  <div className="text-white font-semibold">{member.profession}</div>
                  <div className="text-sm text-gray-400">
                    {member.role}
                    {member.playerName && ` • ${member.playerName}`}
                  </div>
                </div>
              </div>
              <button
                onClick={() => removeMember(member.id)}
                className="text-red-400 hover:text-red-300 p-2 rounded hover:bg-gray-700 transition-colors"
              >
                <X size={20} />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Analyze Button */}
      {team.length >= 2 && onAnalyze && (
        <button
          onClick={() => onAnalyze(team)}
          className="w-full bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 text-white py-3 rounded-lg font-semibold transition-all"
        >
          Analyze Team Synergy
        </button>
      )}
    </div>
  );
};
