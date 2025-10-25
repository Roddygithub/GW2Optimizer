/**
 * VersionDisplay - Composant pour afficher la version de l'application
 * 
 * Peut être utilisé dans les paramètres, le footer, ou n'importe où ailleurs.
 */

import { Info } from 'lucide-react';
import { useAppVersion } from '../../hooks/useAppVersion';
import { Button } from './button';

interface VersionDisplayProps {
  variant?: 'inline' | 'card' | 'minimal';
  showButton?: boolean;
}

export const VersionDisplay = ({ 
  variant = 'inline', 
  showButton = true 
}: VersionDisplayProps) => {
  const { version, name, subtitle, showVersion } = useAppVersion();

  if (variant === 'minimal') {
    return (
      <span className="text-xs text-muted-foreground">
        v{version}
      </span>
    );
  }

  if (variant === 'card') {
    return (
      <div className="p-4 bg-accent/50 rounded-lg space-y-2">
        <div className="flex items-center gap-2">
          <Info className="h-4 w-4 text-gw2-gold" />
          <span className="text-sm font-semibold text-foreground">
            {name}
          </span>
        </div>
        <div className="text-xs text-muted-foreground space-y-1">
          <p>Version: <span className="text-gw2-gold font-medium">v{version}</span></p>
          <p>{subtitle}</p>
        </div>
        {showButton && (
          <Button 
            variant="outline" 
            size="sm" 
            onClick={showVersion}
            className="w-full mt-2"
          >
            Détails de version
          </Button>
        )}
      </div>
    );
  }

  // variant === 'inline'
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-muted-foreground">
        {name} v{version}
      </span>
      {showButton && (
        <Button 
          variant="ghost" 
          size="sm" 
          onClick={showVersion}
          className="h-6 px-2"
        >
          <Info className="h-3 w-3" />
        </Button>
      )}
    </div>
  );
};

export default VersionDisplay;
