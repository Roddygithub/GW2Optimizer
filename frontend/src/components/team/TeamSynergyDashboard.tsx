import React from 'react';
import { Gauge, Shield, AlertTriangle, Users, Sparkles, Brain } from 'lucide-react';
import { Card, CardHeader, CardContent, CardTitle } from '../ui/card';
import { cn } from '../../utils/cn';
import { BuildGroupCard, Build } from '../builds/BuildGroupCard';

export interface TeamMetadata {
  source?: 'mistral' | 'rule-based' | 'hybrid' | string;
  model?: string;
  timestamp?: string;
  context?: string;
  [key: string]: string | number | undefined;
}

export interface TeamSynergyDashboardProps {
  name: string;
  size: number;
  gameMode: string;
  synergyScore: number;
  strategy?: string;
  strengths?: string[];
  weaknesses?: string[];
  builds: Build[];
  metadata?: TeamMetadata;
}

const scoreColor = (score: number) => {
  if (score >= 8) return 'text-emerald-500';
  if (score >= 6) return 'text-amber-500';
  return 'text-red-500';
};

const scoreLabel = (score: number) => {
  if (score >= 8) return 'Excellent';
  if (score >= 6) return 'Solide';
  return 'À améliorer';
};

const Section: React.FC<{ title: string; icon?: React.ReactNode; children: React.ReactNode; className?: string }> = ({
  title,
  icon,
  children,
  className,
}) => (
  <div className={cn('space-y-3', className)}>
    <div className="flex items-center gap-2 text-sm font-semibold text-muted-foreground uppercase tracking-wide">
      {icon}
      <span>{title}</span>
    </div>
    <div className="rounded-xl border border-border/60 bg-background/60 p-4 text-sm leading-relaxed text-foreground shadow-sm">
      {children}
    </div>
  </div>
);

export const TeamSynergyDashboard: React.FC<TeamSynergyDashboardProps> = ({
  name,
  size,
  gameMode,
  synergyScore,
  strategy,
  strengths = [],
  weaknesses = [],
  builds,
  metadata,
}) => {
  const totalBuilds = builds.length;

  return (
    <Card className="border-gw2-gold/20 bg-background/95 shadow-2xl">
      <CardHeader className="border-b border-gw2-gold/20">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-2">
            <CardTitle className="text-2xl font-bold text-gw2-gold">
              {name}
            </CardTitle>
            <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
              <span className="inline-flex items-center gap-1 rounded-md border border-gw2-gold/40 bg-gw2-gold/10 px-2 py-1 font-medium uppercase tracking-wide">
                <Users className="h-3 w-3" />
                {size} joueurs
              </span>
              <span className="rounded-md border border-border/60 bg-border/10 px-2 py-1 text-xs uppercase tracking-wide">
                {gameMode}
              </span>
              <span className="text-muted-foreground/80">
                {totalBuilds} builds uniques
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3 rounded-xl border border-border/80 bg-background/80 px-4 py-3 text-muted-foreground">
            <Gauge className={cn('h-10 w-10', scoreColor(synergyScore))} />
            <div>
              <p className="text-xs uppercase tracking-wide text-muted-foreground/80">Score Synergie</p>
              <p className={cn('text-2xl font-bold', scoreColor(synergyScore))}>{synergyScore.toFixed(1)}</p>
              <p className="text-xs text-muted-foreground/70">{scoreLabel(synergyScore)}</p>
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-8 py-6">
        {strategy && (
          <Section title="Stratégie recommandée" icon={<Brain className="h-4 w-4 text-gw2-gold" />}>
            <p className="text-sm text-muted-foreground whitespace-pre-wrap">{strategy}</p>
          </Section>
        )}

        <Section title="Composition" icon={<Sparkles className="h-4 w-4 text-gw2-gold" />}>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {builds.map((build) => (
              <BuildGroupCard key={build.id} build={build} playerCount={(build as Build & { playerCount?: number }).playerCount || 1} />
            ))}
          </div>
        </Section>

        <div className="grid gap-6 md:grid-cols-2">
          <Section title="Forces" icon={<Shield className="h-4 w-4 text-emerald-500" />}>
            {strengths.length ? (
              <ul className="space-y-2 text-sm text-emerald-500">
                {strengths.map((item) => (
                  <li key={item} className="flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-emerald-500" />
                    {item}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-muted-foreground/70">Aucun point fort saillant détecté.</p>
            )}
          </Section>

          <Section title="Points d'attention" icon={<AlertTriangle className="h-4 w-4 text-amber-500" />}>
            {weaknesses.length ? (
              <ul className="space-y-2 text-sm text-amber-500">
                {weaknesses.map((item) => (
                  <li key={item} className="flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-amber-500" />
                    {item}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-muted-foreground/70">Aucun risque majeur identifié.</p>
            )}
          </Section>
        </div>

        {metadata && Object.keys(metadata).length > 0 && (
          <Section title="Métadonnées">
            <dl className="grid gap-3 text-xs md:grid-cols-2">
              {Object.entries(metadata).map(([key, value]) => (
                <div key={key} className="flex justify-between gap-2 rounded border border-border/50 bg-background/60 px-3 py-2">
                  <span className="text-muted-foreground uppercase tracking-wide">{key}</span>
                  <span className="font-medium text-foreground">{String(value)}</span>
                </div>
              ))}
            </dl>
          </Section>
        )}
      </CardContent>
    </Card>
  );
};

export default TeamSynergyDashboard;
