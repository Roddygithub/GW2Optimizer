import React from 'react';
import { X, Users, Sword, Shield, Heart, Zap, Sparkles } from 'lucide-react';
import { Build } from './BuildGroupCard';
import { Card, CardHeader, CardContent, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { cn } from '../../utils/cn';

export interface DetailedBuild extends Build {
  priority?: 'High' | 'Medium' | 'Low' | string;
  specialization?: string;
  boons?: string[];
  utilities?: string[];
  eliteSkill?: string;
  rune?: string;
  notes?: string;
  metadata?: Record<string, string | number | undefined>;
}

export interface BuildDetailPanelProps {
  build: DetailedBuild;
  playerCount?: number;
  onClose?: () => void;
  className?: string;
}

const Section: React.FC<{ title: string; icon?: React.ReactNode; children: React.ReactNode }> = ({
  title,
  icon,
  children,
}) => (
  <div className="space-y-3">
    <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground uppercase tracking-wide">
      {icon}
      <span>{title}</span>
    </div>
    <div className="rounded-lg border border-border/60 bg-background/60 p-4 text-sm leading-relaxed text-foreground">
      {children}
    </div>
  </div>
);

export const BuildDetailPanel: React.FC<BuildDetailPanelProps> = ({ build, playerCount, onClose, className }) => {
  const {
    name,
    role,
    profession,
    weapons,
    traits = [],
    skills = [],
    stats = {},
    priority,
    specialization,
    boons = [],
    utilities = [],
    eliteSkill,
    rune,
    notes,
    metadata,
  } = build;

  const renderList = (items: Array<string | undefined>, emptyLabel: string) => {
    const filtered = items.filter(Boolean) as string[];
    if (!filtered.length) {
      return <span className="text-muted-foreground/70 text-sm">{emptyLabel}</span>;
    }

    return (
      <ul className="flex flex-wrap gap-2">
        {filtered.map((item) => (
          <li
            key={item}
            className="rounded-full bg-gw2-gold/10 px-3 py-1 text-xs font-medium text-gw2-gold shadow-sm"
          >
            {item}
          </li>
        ))}
      </ul>
    );
  };

  const statEntries = Object.entries(stats).filter(([, value]) => value !== undefined && value !== null);

  return (
    <Card className={cn('relative max-h-[90vh] overflow-y-auto border-gw2-gold/30 bg-background/95 shadow-2xl', className)}>
      <CardHeader className="sticky top-0 z-10 border-b border-gw2-gold/20 bg-background/95 pb-4">
        <div className="flex items-start justify-between gap-4">
          <div>
            <CardTitle className="flex items-center gap-3 text-2xl font-bold text-gw2-gold">
              <Sparkles className="h-5 w-5" />
              {name}
            </CardTitle>
            <div className="mt-2 flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
              <span className="rounded-md border border-gw2-gold/40 px-2 py-1 font-medium uppercase tracking-wide">
                {profession}
              </span>
              {specialization && (
                <span className="rounded-md border border-border/70 bg-border/10 px-2 py-1 text-xs uppercase tracking-wide">
                  {specialization}
                </span>
              )}
              <span>{role}</span>
              {priority && (
                <span className="rounded-md bg-gw2-gold/15 px-2 py-1 text-xs font-semibold uppercase text-gw2-gold">
                  Priorité : {priority}
                </span>
              )}
              {playerCount && playerCount > 1 && (
                <span className="inline-flex items-center gap-1 rounded-full bg-gw2-gold/10 px-2 py-1 text-xs font-medium text-gw2-gold">
                  <Users className="h-3 w-3" />
                  x{playerCount}
                </span>
              )}
            </div>
          </div>

          {onClose && (
            <Button variant="ghost" size="icon" onClick={onClose} className="shrink-0" aria-label="Fermer le détail du build">
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-8 py-6">
        <Section
          title="Boons clés"
          icon={<Sparkles className="h-4 w-4 text-gw2-gold" />}
        >
          {renderList(boons, "Aucun boon principal spécifié")}
        </Section>

        <Section
          title="Armes"
          icon={<Sword className="h-4 w-4 text-gw2-gold" />}
        >
          <div className="grid gap-3 text-sm">
            {weapons.twoHanded ? (
              <div>
                <p className="font-semibold text-foreground">Arme à deux mains</p>
                <p className="text-muted-foreground">{weapons.twoHanded}</p>
              </div>
            ) : (
              <>
                <div>
                  <p className="font-semibold text-foreground">Main principale</p>
                  <p className="text-muted-foreground">{weapons.mainHand || 'Non spécifié'}</p>
                </div>
                <div>
                  <p className="font-semibold text-foreground">Main secondaire</p>
                  <p className="text-muted-foreground">{weapons.offHand || 'Non spécifié'}</p>
                </div>
              </>
            )}
          </div>
        </Section>

        <Section title="Traits" icon={<Shield className="h-4 w-4 text-gw2-gold" />}>
          {renderList(traits, 'Aucun trait fourni par l\'IA')}
        </Section>

        <Section title="Compétences" icon={<Zap className="h-4 w-4 text-gw2-gold" />}>
          <div className="space-y-3">
            {renderList(skills.slice(0, 5), 'Compétences non spécifiées')}
            {(utilities.length > 0 || eliteSkill) && (
              <div className="space-y-2 text-sm text-muted-foreground">
                {renderList(utilities, 'Utilitaires non spécifiés')}
                {eliteSkill && (
                  <div className="rounded-md border border-gw2-gold/30 bg-gw2-gold/5 px-3 py-2 text-xs font-semibold uppercase tracking-wide text-gw2-gold">
                    Elite : {eliteSkill}
                  </div>
                )}
              </div>
            )}
          </div>
        </Section>

        <Section title="Statistiques recommandées" icon={<Heart className="h-4 w-4 text-gw2-gold" />}>
          {statEntries.length ? (
            <div className="grid gap-2 text-sm md:grid-cols-2">
              {statEntries.map(([key, value]) => (
                <div key={key} className="flex justify-between rounded-lg border border-border/60 bg-background/60 px-3 py-2">
                  <span className="text-muted-foreground capitalize">{key}</span>
                  <span className="font-semibold text-foreground">{value}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground/80">Aucune statistique fournie par l'IA.</p>
          )}
        </Section>

        {rune && (
          <Section title="Rune recommandée">
            <p className="text-sm text-foreground">{rune}</p>
          </Section>
        )}

        {notes && (
          <Section title="Notes de l'IA">
            <p className="text-sm text-muted-foreground whitespace-pre-wrap">{notes}</p>
          </Section>
        )}

        {metadata && Object.keys(metadata).length > 0 && (
          <Section title="Métadonnées">
            <dl className="grid gap-2 text-xs md:grid-cols-2">
              {Object.entries(metadata).map(([key, value]) => (
                <div key={key} className="flex justify-between gap-2 rounded border border-border/60 bg-background/60 px-3 py-2">
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

export default BuildDetailPanel;
