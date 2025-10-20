import React, { useState } from 'react';
import apiClient from '../services/api';

interface Analysis {
  strengths: string[];
  weaknesses: string[];
  suggestions: string[];
}

const TeamAnalyzer: React.FC = () => {
  const [teamComp, setTeamComp] = useState('Guardian, Guardian, Warrior, Revenant, Mesmer');
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setAnalysis(null);

    const professions = teamComp.split(',').map(p => p.trim()).filter(p => p);

    try {
      const response = await apiClient.post('/ai/analyze-team-synergy', { professions });
      setAnalysis(response.data);
    } catch (err) {
      setError('Failed to get analysis. The AI service might be busy.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold mb-4 text-gw2-gold">Team Synergy Analyzer</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="teamComp" className="block text-sm font-medium">Team Composition (comma-separated)</label>
          <textarea
            id="teamComp"
            value={teamComp}
            onChange={(e) => setTeamComp(e.target.value)}
            rows={2}
            className="w-full mt-1 bg-gray-700 border-gray-600 rounded-md"
          />
        </div>
        <button type="submit" disabled={isLoading} className="w-full px-4 py-2 font-bold text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:bg-gray-500">
          {isLoading ? 'Analyzing...' : 'Analyze Team'}
        </button>
      </form>

      {error && <p className="mt-4 text-sm text-red-400">{error}</p>}

      {analysis && (
        <div className="mt-6 space-y-4">
          <div>
            <h4 className="font-semibold text-green-400">Strengths:</h4>
            <ul className="list-disc list-inside text-gray-300">
              {analysis.strengths.map((item, index) => <li key={index}>{item}</li>)}
            </ul>
          </div>
          <div>
            <h4 className="font-semibold text-red-400">Weaknesses:</h4>
            <ul className="list-disc list-inside text-gray-300">
              {analysis.weaknesses.map((item, index) => <li key={index}>{item}</li>)}
            </ul>
          </div>
          <div>
            <h4 className="font-semibold text-yellow-400">Suggestions:</h4>
            <ul className="list-disc list-inside text-gray-300">
              {analysis.suggestions.map((item, index) => <li key={index}>{item}</li>)}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};

export default TeamAnalyzer;