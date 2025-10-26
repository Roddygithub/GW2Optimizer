import React from 'react';
import { Bot, User, Sword } from 'lucide-react';
import { cn } from '../../utils/cn';
import { Button } from '../ui/button';
import BuildGroupCard from '../builds/BuildGroupCard';

export interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  builds?: Array<{
    id?: string;
    name?: string;
    profession: string;
    role?: string;
    weapons?: Record<string, unknown>;
    traits?: string[];
    skills?: string[];
    stats?: Record<string, unknown>;
    playerCount?: number;
  }>;
  suggestions?: string[];
}

interface ChatMessageProps {
  message: Message;
  onSuggestionClick?: (suggestion: string) => void;
  className?: string;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message, onSuggestionClick }) => {
  const formatMessageContent = (content: string) =>
    content.split('\n').map((line, i) => (
      <React.Fragment key={i}>
        {line}
        <br />
      </React.Fragment>
    ));

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
  };

  const hasBuilds = (msg: Message): msg is Message & { builds: NonNullable<Message['builds']> } => {
    return Array.isArray(msg.builds) && msg.builds.length > 0;
  };

  const hasSuggestions = (msg: Message): msg is Message & { suggestions: string[] } => {
    return Array.isArray(msg.suggestions) && msg.suggestions.length > 0;
  };

  return (
    <div className={cn('flex gap-3 max-w-[90%]', message.role === 'user' ? 'ml-auto' : 'mr-auto')}>
      <div
        className={cn(
          'flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center',
          message.role === 'user' ? 'bg-gw2-gold/10 text-gw2-gold' : 'bg-gw2-blue/10 text-gw2-blue'
        )}
      >
        {message.role === 'user' ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>
      <div
        className={cn(
          'p-3 rounded-2xl text-sm',
          message.role === 'user'
            ? 'bg-gw2-gold/10 text-foreground rounded-tr-none'
            : 'bg-muted text-foreground rounded-tl-none',
          'relative group w-full max-w-[90%] md:max-w-[80%]'
        )}
      >
        <div className="whitespace-pre-wrap">{formatMessageContent(message.content)}</div>

        {hasBuilds(message) && (
          <div className="mt-4 space-y-3">
            <div className="text-sm font-semibold text-foreground flex items-center border-b border-border pb-1 mb-2">
              <Sword className="h-4 w-4 mr-2 text-gw2-gold" />
              Builds suggérés
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {message.builds.map((build, idx) => {
                if (!build.profession) {
                  console.warn('Build sans profession, ignoré:', build);
                  return null;
                }

                const buildId = build.id || `build-${idx}`;
                const buildName = build.name || `Build ${build.profession} ${idx + 1}`;
                const buildRole = build.role || 'DPS';
                const buildWeapons = build.weapons || {};
                const buildTraits = build.traits || [];
                const buildSkills = build.skills || [];
                const buildStats = build.stats || {};
                const buildPlayerCount = build.playerCount || 1;

                return (
                  <BuildGroupCard
                    key={buildId}
                    build={{
                      id: buildId,
                      name: buildName,
                      profession: build.profession,
                      role: buildRole,
                      weapons: buildWeapons,
                      traits: buildTraits,
                      skills: buildSkills,
                      stats: buildStats,
                    }}
                    playerCount={buildPlayerCount}
                    className="w-full h-full"
                  />
                );
              })}
            </div>
          </div>
        )}

        {hasSuggestions(message) && onSuggestionClick && (
          <div className="mt-4 pt-3 border-t border-border">
            <div className="text-xs font-medium text-muted-foreground mb-2">
              Suggestions de suivi :
            </div>
            <div className="flex flex-wrap gap-2">
              {message.suggestions.map((suggestion, idx) => (
                <Button
                  key={idx}
                  variant="outline"
                  size="sm"
                  className="text-xs h-8"
                  onClick={() => onSuggestionClick(suggestion)}
                  role="button"
                  aria-label={`Suggestion: ${suggestion}`}
                  data-testid={`suggestion-${suggestion.toLowerCase().replace(/\s+/g, '-')}`}
                >
                  {suggestion}
                </Button>
              ))}
            </div>
          </div>
        )}

        <span className="text-xs opacity-50 mt-2 block text-right">
          {formatTime(message.timestamp)}
        </span>
      </div>
    </div>
  );
};

export default ChatMessage;
