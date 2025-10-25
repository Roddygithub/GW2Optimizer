/**
 * BuildGroupCard - Composant pour afficher un build avec le nombre de joueurs assignés
 * 
 * Affiche les détails d'un build : profession, traits, armes, skills, statistiques
 * Regroupe les builds identiques et affiche le nombre de joueurs
 */

import { Users, Sword, Shield, Heart, Zap } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { cn } from '../../utils/cn';

// Mapping des professions vers leurs couleurs
const professionColors: Record<string, string> = {
  guardian: 'text-profession-guardian border-profession-guardian/30',
  warrior: 'text-profession-warrior border-profession-warrior/30',
  engineer: 'text-profession-engineer border-profession-engineer/30',
  ranger: 'text-profession-ranger border-profession-ranger/30',
  thief: 'text-profession-thief border-profession-thief/30',
  elementalist: 'text-profession-elementalist border-profession-elementalist/30',
  mesmer: 'text-profession-mesmer border-profession-mesmer/30',
  necromancer: 'text-profession-necromancer border-profession-necromancer/30',
  revenant: 'text-profession-revenant border-profession-revenant/30',
};

export interface Build {
  id: string;
  name: string;
  profession: string;
  role: string;
  weapons: {
    mainHand?: string;
    offHand?: string;
    twoHanded?: string;
  };
  traits: string[];
  skills: string[];
  stats: {
    power?: number;
    precision?: number;
    toughness?: number;
    vitality?: number;
    condition?: number;
    healing?: number;
  };
}

export interface BuildGroupCardProps {
  build: Build;
  playerCount: number;
  className?: string;
}

export const BuildGroupCard = ({ build, playerCount, className }: BuildGroupCardProps) => {
  const professionColor = professionColors[build.profession.toLowerCase()] || 'text-foreground border-border';

  return (
    <Card className={cn('hover:shadow-glow transition-shadow', professionColor, className)}>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg font-bold flex items-center gap-2">
              {build.name}
              {playerCount > 1 && (
                <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-gw2-gold/20 text-gw2-gold text-xs font-medium">
                  <Users className="h-3 w-3" />
                  x{playerCount}
                </span>
              )}
            </CardTitle>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-sm font-medium capitalize">{build.profession}</span>
              <span className="text-xs text-muted-foreground">•</span>
              <span className="text-sm text-muted-foreground">{build.role}</span>
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Weapons */}
        <div>
          <h4 className="text-xs font-semibold text-muted-foreground mb-2 flex items-center gap-1">
            <Sword className="h-3 w-3" />
            Armes
          </h4>
          <div className="flex flex-wrap gap-2">
            {build.weapons.twoHanded ? (
              <span className="px-2 py-1 rounded bg-accent text-xs">
                {build.weapons.twoHanded}
              </span>
            ) : (
              <>
                {build.weapons.mainHand && (
                  <span className="px-2 py-1 rounded bg-accent text-xs">
                    {build.weapons.mainHand}
                  </span>
                )}
                {build.weapons.offHand && (
                  <span className="px-2 py-1 rounded bg-accent text-xs">
                    {build.weapons.offHand}
                  </span>
                )}
              </>
            )}
          </div>
        </div>

        {/* Traits */}
        {build.traits && build.traits.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-muted-foreground mb-2 flex items-center gap-1">
              <Shield className="h-3 w-3" />
              Traits
            </h4>
            <div className="flex flex-wrap gap-1">
              {build.traits.slice(0, 3).map((trait, idx) => (
                <span
                  key={idx}
                  className="px-2 py-1 rounded bg-gw2-gold/10 text-gw2-gold text-xs"
                >
                  {trait}
                </span>
              ))}
              {build.traits.length > 3 && (
                <span className="px-2 py-1 rounded bg-muted text-xs text-muted-foreground">
                  +{build.traits.length - 3}
                </span>
              )}
            </div>
          </div>
        )}

        {/* Skills */}
        {build.skills && build.skills.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-muted-foreground mb-2 flex items-center gap-1">
              <Zap className="h-3 w-3" />
              Compétences
            </h4>
            <div className="flex flex-wrap gap-1">
              {build.skills.slice(0, 5).map((skill, idx) => (
                <span
                  key={idx}
                  className="px-2 py-1 rounded bg-accent text-xs"
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Stats */}
        {build.stats && Object.keys(build.stats).length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-muted-foreground mb-2 flex items-center gap-1">
              <Heart className="h-3 w-3" />
              Statistiques
            </h4>
            <div className="grid grid-cols-2 gap-2 text-xs">
              {build.stats.power && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Puissance:</span>
                  <span className="font-medium">{build.stats.power}</span>
                </div>
              )}
              {build.stats.precision && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Précision:</span>
                  <span className="font-medium">{build.stats.precision}</span>
                </div>
              )}
              {build.stats.toughness && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Robustesse:</span>
                  <span className="font-medium">{build.stats.toughness}</span>
                </div>
              )}
              {build.stats.vitality && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Vitalité:</span>
                  <span className="font-medium">{build.stats.vitality}</span>
                </div>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default BuildGroupCard;
