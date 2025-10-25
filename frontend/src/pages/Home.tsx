import { useState } from 'react';
import { Bot, Sparkles, Users } from 'lucide-react';
import { ChatBox } from '../components/ai/ChatBox';
import { BuildGroupCard, Build } from '../components/builds/BuildGroupCard';
import { APP_NAME, APP_VERSION, APP_FULL_TITLE } from '../config/version';

export const Home = () => {
  // État pour stocker les builds générés par l'IA
  const [generatedBuilds, setGeneratedBuilds] = useState<Array<{ build: Build; count: number }>>([]);

  // Fonction pour regrouper les builds identiques
  const groupBuilds = (builds: Build[]) => {
    const grouped = new Map<string, { build: Build; count: number }>();
    
    builds.forEach((build) => {
      const key = `${build.profession}-${build.name}-${build.role}`;
      const existing = grouped.get(key);
      
      if (existing) {
        existing.count++;
      } else {
        grouped.set(key, { build, count: 1 });
      }
    });
    
    return Array.from(grouped.values());
  };

  // Fonction appelée quand l'IA génère des builds
  const handleBuildsGenerated = (builds: Build[]) => {
    const grouped = groupBuilds(builds);
    setGeneratedBuilds(grouped);
  };

  return (
    <div className="space-y-8 relative min-h-screen">
      {/* ChatBox IA - Toujours visible */}
      <ChatBox defaultOpen={true} className="z-40" />
      
      {/* Hero Section */}
      <section className="text-center space-y-6 py-8">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gw2-gold/10 border border-gw2-gold/30">
          <Bot className="h-4 w-4 text-gw2-gold" />
          <span className="text-sm text-gw2-gold font-medium">{APP_FULL_TITLE}</span>
        </div>
        
        <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-gw2-gold via-gw2-blue to-gw2-purple bg-clip-text text-transparent">
          Assistant IA pour Compositions WvW
        </h1>
        
        <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
          Utilisez l'intelligence artificielle Mistral pour générer et optimiser vos compositions d'escouade WvW
        </p>
        
        <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
          <Sparkles className="h-4 w-4 text-gw2-gold" />
          <span>Propulsé par Ollama avec Mistral</span>
        </div>
      </section>

      {/* Builds générés par l'IA */}
      {generatedBuilds.length > 0 && (
        <section className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold flex items-center gap-2">
                <Users className="h-6 w-6 text-gw2-gold" />
                Composition Générée
              </h2>
              <p className="text-sm text-muted-foreground mt-1">
                {generatedBuilds.reduce((acc, { count }) => acc + count, 0)} joueurs • {generatedBuilds.length} builds uniques
              </p>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {generatedBuilds.map(({ build, count }, idx) => (
              <BuildGroupCard
                key={`${build.id}-${idx}`}
                build={build}
                playerCount={count}
              />
            ))}
          </div>
        </section>
      )}

      {/* Instructions d'utilisation */}
      {generatedBuilds.length === 0 && (
        <section className="text-center space-y-6 py-12 px-6 rounded-2xl bg-gradient-to-r from-gw2-gold/10 via-gw2-blue/10 to-gw2-purple/10 border border-gw2-gold/20">
          <Bot className="h-16 w-16 text-gw2-gold mx-auto" />
          <h2 className="text-2xl font-bold">Comment utiliser l'Assistant IA ?</h2>
          <div className="max-w-2xl mx-auto space-y-4 text-left">
            <div className="p-4 rounded-lg bg-background/50">
              <h3 className="font-semibold mb-2">1. Ouvrez la ChatBox</h3>
              <p className="text-sm text-muted-foreground">
                Cliquez sur le bouton de chat en bas à droite pour ouvrir l'assistant IA.
              </p>
            </div>
            <div className="p-4 rounded-lg bg-background/50">
              <h3 className="font-semibold mb-2">2. Décrivez votre besoin</h3>
              <p className="text-sm text-muted-foreground">
                Demandez une composition d'escouade, par exemple : "Crée-moi une composition de 50 joueurs pour le WvW avec un bon équilibre entre DPS et support"
              </p>
            </div>
            <div className="p-4 rounded-lg bg-background/50">
              <h3 className="font-semibold mb-2">3. Visualisez les résultats</h3>
              <p className="text-sm text-muted-foreground">
                L'IA génère une composition optimisée qui s'affiche automatiquement ci-dessous avec tous les détails des builds.
              </p>
            </div>
          </div>
        </section>
      )}
      {/* Footer */}
      <footer className="text-center text-xs text-muted-foreground/70 py-8 border-t border-border mt-12">
        <p className="font-medium">{APP_NAME} v{APP_VERSION}</p>
        <p className="mt-2">Propulsé par Ollama avec Mistral</p>
        <p className="mt-1">© 2025 - WvW McM Dashboard - Tous droits réservés</p>
      </footer>
    </div>
  );
};
