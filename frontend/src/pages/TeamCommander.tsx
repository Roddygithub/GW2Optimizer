import { useState } from 'react';
import { Send, Users, Sparkles, Shield, Zap } from 'lucide-react';
import { teamCommanderApi } from '../services/api';
import TeamDisplay from '../components/TeamDisplay.tsx';

interface TeamData {
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
    }>;
  }>;
  synergy: {
    score: string;
    details: Record<string, string>;
  };
  notes: string[];
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  teamData?: TeamData;
  timestamp: Date;
}

export default function TeamCommander() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [experience, setExperience] = useState<'beginner' | 'intermediate' | 'expert'>('intermediate');
  const [mode, setMode] = useState<'wvw_zerg' | 'wvw_outnumber' | 'wvw_roam'>('wvw_zerg');

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await teamCommanderApi.command(input, experience, mode);

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `✅ Team créée avec succès ! Synergie: ${response.synergy.score}`,
        teamData: response,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error: unknown) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `❌ Erreur: ${error instanceof Error ? error.message : 'Impossible de créer la team'}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const quickCommands = [
    {
      icon: Shield,
      label: 'Zerg Standard',
      command: '2 groupes de 5 avec Firebrand, Druid, Herald, Spellbreaker, Reaper',
    },
    {
      icon: Zap,
      label: 'Outnumber',
      command: '1 groupe de 5 avec Firebrand, Spellbreaker, Deadeye, Holosmith, Willbender',
    },
    {
      icon: Users,
      label: 'Par Rôles',
      command: 'Je veux 10 joueurs. Dans chaque groupe : stabeur, healer, booner, strip, dps',
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Header */}
      <div className="border-b border-purple-500/20 bg-slate-900/50 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-500/20 rounded-lg">
              <Sparkles className="w-6 h-6 text-purple-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">AI Team Commander</h1>
              <p className="text-sm text-gray-400">
                Décrivez votre team, l'IA construit tout automatiquement
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-6 max-w-6xl">
        {/* Quick Commands */}
        {messages.length === 0 && (
          <div className="mb-6 space-y-3">
            <h2 className="text-sm font-medium text-gray-400 uppercase tracking-wider">
              Templates Rapides
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {quickCommands.map((cmd) => (
                <button
                  key={cmd.label}
                  onClick={() => setInput(cmd.command)}
                  className="p-4 bg-slate-800/50 hover:bg-slate-800 border border-purple-500/20 rounded-lg transition-all group"
                >
                  <div className="flex items-center gap-3 mb-2">
                    <cmd.icon className="w-5 h-5 text-purple-400 group-hover:text-purple-300" />
                    <span className="font-medium text-white">{cmd.label}</span>
                  </div>
                  <p className="text-xs text-gray-400 text-left line-clamp-2">{cmd.command}</p>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Messages */}
        <div className="space-y-4 mb-6">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-3xl ${
                  message.role === 'user'
                    ? 'bg-purple-600 text-white'
                    : 'bg-slate-800 text-gray-100'
                } rounded-lg p-4 shadow-lg`}
              >
                <p className="whitespace-pre-wrap">{message.content}</p>
                {message.teamData && <TeamDisplay data={message.teamData} />}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-slate-800 rounded-lg p-4 shadow-lg">
                <div className="flex items-center gap-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-purple-400 border-t-transparent" />
                  <span className="text-gray-400">L'IA réfléchit...</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Input */}
        <div className="sticky bottom-0 bg-slate-900/90 backdrop-blur-sm border border-purple-500/20 rounded-lg p-4 space-y-3">
          {/* Team Experience Selector */}
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="text-xs text-gray-400 uppercase tracking-wider">Niveau de l'équipe</div>
            <div className="flex items-center gap-2 text-xs">
              <button
                type="button"
                onClick={() => setExperience('beginner')}
                className={`px-3 py-1 rounded-full border text-xs transition-colors ${
                  experience === 'beginner'
                    ? 'bg-purple-600 text-white border-purple-400'
                    : 'bg-slate-800 text-gray-300 border-purple-500/30 hover:border-purple-400/60'
                }`}
              >
                Débutant
              </button>
              <button
                type="button"
                onClick={() => setExperience('intermediate')}
                className={`px-3 py-1 rounded-full border text-xs transition-colors ${
                  experience === 'intermediate'
                    ? 'bg-purple-600 text-white border-purple-400'
                    : 'bg-slate-800 text-gray-300 border-purple-500/30 hover:border-purple-400/60'
                }`}
              >
                Intermédiaire
              </button>
              <button
                type="button"
                onClick={() => setExperience('expert')}
                className={`px-3 py-1 rounded-full border text-xs transition-colors ${
                  experience === 'expert'
                    ? 'bg-purple-600 text-white border-purple-400'
                    : 'bg-slate-800 text-gray-300 border-purple-500/30 hover:border-purple-400/60'
                }`}
              >
                Expert
              </button>
            </div>
          </div>

          {/* WvW Mode Selector */}
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="text-xs text-gray-400 uppercase tracking-wider">Mode de jeu</div>
            <div className="flex items-center gap-2 text-xs">
              <button
                type="button"
                onClick={() => setMode('wvw_zerg')}
                className={`px-3 py-1 rounded-full border text-xs transition-colors ${
                  mode === 'wvw_zerg'
                    ? 'bg-purple-600 text-white border-purple-400'
                    : 'bg-slate-800 text-gray-300 border-purple-500/30 hover:border-purple-400/60'
                }`}
              >
                Zerg
              </button>
              <button
                type="button"
                onClick={() => setMode('wvw_outnumber')}
                className={`px-3 py-1 rounded-full border text-xs transition-colors ${
                  mode === 'wvw_outnumber'
                    ? 'bg-purple-600 text-white border-purple-400'
                    : 'bg-slate-800 text-gray-300 border-purple-500/30 hover:border-purple-400/60'
                }`}
              >
                Outnumber
              </button>
              <button
                type="button"
                onClick={() => setMode('wvw_roam')}
                className={`px-3 py-1 rounded-full border text-xs transition-colors ${
                  mode === 'wvw_roam'
                    ? 'bg-purple-600 text-white border-purple-400'
                    : 'bg-slate-800 text-gray-300 border-purple-500/30 hover:border-purple-400/60'
                }`}
              >
                Roam
              </button>
            </div>
          </div>

          <div className="flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
              placeholder="Ex: Je veux 2 groupes de 5 avec Firebrand, Druid, Harbinger..."
              className="flex-1 bg-slate-800 text-white placeholder-gray-500 border border-purple-500/20 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500"
              disabled={isLoading}
            />
            <button
              onClick={handleSend}
              disabled={isLoading || !input.trim()}
              className="px-6 py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-slate-700 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors flex items-center gap-2"
            >
              <Send className="w-4 h-4" />
              <span className="hidden sm:inline">Envoyer</span>
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            💡 Astuce: Soyez précis sur les classes ou les rôles souhaités
          </p>
        </div>
      </div>
    </div>
  );
}
