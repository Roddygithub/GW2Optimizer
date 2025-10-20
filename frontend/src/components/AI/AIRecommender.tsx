import React, { useState } from 'react';
import apiClient from '../services/api';

interface Recommendation {
  build_name: string;
  description: string;
  synergies: string[];
}

const AIRecommender: React.FC = () => {
  const [profession, setProfession] = useState('Guardian');
  const [role, setRole] = useState('Support');
  const [gameMode, setGameMode] = useState('WvW Zerg');
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setRecommendation(null);

    try {
      const response = await apiClient.post('/ai/recommend-build', {
        profession,
        role,
        game_mode: gameMode,
      });
      setRecommendation(response.data);
    } catch (err) {
      setError('Failed to get recommendation. The AI service might be busy.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold mb-4 text-gw2-gold">Build Recommender</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label htmlFor="profession" className="block text-sm font-medium">Profession</label>
            <select id="profession" value={profession} onChange={(e) => setProfession(e.target.value)} className="w-full mt-1 bg-gray-700 border-gray-600 rounded-md">
              {['Guardian', 'Revenant', 'Warrior', 'Engineer', 'Ranger', 'Thief', 'Elementalist', 'Mesmer', 'Necromancer'].map(p => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
          <div>
            <label htmlFor="role" className="block text-sm font-medium">Role</label>
            <input id="role" type="text" value={role} onChange={(e) => setRole(e.target.value)} className="w-full mt-1 bg-gray-700 border-gray-600 rounded-md" />
          </div>
          <div>
            <label htmlFor="gameMode" className="block text-sm font-medium">Game Mode</label>
            <input id="gameMode" type="text" value={gameMode} onChange={(e) => setGameMode(e.target.value)} className="w-full mt-1 bg-gray-700 border-gray-600 rounded-md" />
          </div>
        </div>
        <button type="submit" disabled={isLoading} className="w-full px-4 py-2 font-bold text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:bg-gray-500">
          {isLoading ? 'Thinking...' : 'Get Recommendation'}
        </button>
      </form>

      {error && <p className="mt-4 text-sm text-red-400">{error}</p>}

      {recommendation && (
        <div className="mt-6 p-4 bg-gray-700/50 rounded-lg">
          <h3 className="text-xl font-semibold text-gw2-gold">{recommendation.build_name}</h3>
          <p className="mt-2 text-gray-300">{recommendation.description}</p>
          <div className="mt-4">
            <h4 className="font-semibold">Key Synergies:</h4>
            <ul className="flex flex-wrap gap-2 mt-2">
              {recommendation.synergies.map((synergy, index) => (
                <li key={index} className="px-2 py-1 text-xs bg-gw2-blue text-white rounded-full">{synergy}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};

export default AIRecommender;