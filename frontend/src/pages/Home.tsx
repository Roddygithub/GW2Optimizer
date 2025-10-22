import { Link } from 'react-router-dom';
import { Shield, Users, Sword, BarChart3, ArrowRight } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';

export const Home = () => {
  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <section className="text-center space-y-6 py-12">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gw2-gold/10 border border-gw2-gold/30">
          <Shield className="h-4 w-4 text-gw2-gold" />
          <span className="text-sm text-gw2-gold font-medium">WvW McM Dashboard v1.7.0</span>
        </div>
        
        <h1 className="text-5xl md:text-6xl font-bold bg-gradient-to-r from-gw2-gold via-gw2-blue to-gw2-purple bg-clip-text text-transparent">
          Optimisez vos Escouades WvW
        </h1>
        
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
          Créez, gérez et optimisez vos compositions d'escouade pour dominer le Monde contre Monde de Guild Wars 2
        </p>
        
        <div className="flex items-center justify-center gap-4">
          <Link to="/dashboard">
            <Button variant="gw2" size="lg" className="gap-2">
              Accéder au Dashboard
              <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
          <Link to="/builds">
            <Button variant="outline" size="lg">
              Explorer les Builds
            </Button>
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Card className="border-profession-guardian/30 hover:shadow-glow transition-shadow">
          <CardHeader>
            <Users className="h-10 w-10 text-profession-guardian mb-2" />
            <CardTitle>Gestion d'Escouades</CardTitle>
            <CardDescription>
              Créez et gérez vos compositions d'escouade avec un système de slots intelligent
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li>• Jusqu'à 50 joueurs par escouade</li>
              <li>• Assignation automatique des rôles</li>
              <li>• Analyse des synergies en temps réel</li>
            </ul>
          </CardContent>
        </Card>

        <Card className="border-profession-warrior/30 hover:shadow-glow transition-shadow">
          <CardHeader>
            <Sword className="h-10 w-10 text-profession-warrior mb-2" />
            <CardTitle>Bibliothèque de Builds</CardTitle>
            <CardDescription>
              Accédez à une vaste collection de builds optimisés pour le WvW
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li>• Builds pour toutes les professions</li>
              <li>• Filtres par rôle et mode de jeu</li>
              <li>• Partage avec la communauté</li>
            </ul>
          </CardContent>
        </Card>

        <Card className="border-gw2-gold/30 hover:shadow-glow transition-shadow">
          <CardHeader>
            <BarChart3 className="h-10 w-10 text-gw2-gold mb-2" />
            <CardTitle>Statistiques Avancées</CardTitle>
            <CardDescription>
              Analysez les performances et optimisez vos stratégies
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li>• Taux de victoire par composition</li>
              <li>• Analyse des synergies d'équipe</li>
              <li>• Recommandations personnalisées</li>
            </ul>
          </CardContent>
        </Card>
      </section>

      {/* CTA Section */}
      <section className="text-center space-y-6 py-12 px-6 rounded-2xl bg-gradient-to-r from-gw2-gold/10 via-gw2-blue/10 to-gw2-purple/10 border border-gw2-gold/20">
        <h2 className="text-3xl font-bold">Prêt à Dominer le WvW ?</h2>
        <p className="text-muted-foreground max-w-xl mx-auto">
          Rejoignez des milliers de commandants qui utilisent GW2 Optimizer pour créer les meilleures compositions d'escouade
        </p>
        <Link to="/register">
          <Button variant="gw2" size="lg">
            Commencer Gratuitement
          </Button>
        </Link>
      </section>

      {/* Footer Note */}
      <div className="text-center text-xs text-muted-foreground/70 py-4">
        <p>Empowered by Ollama with Mistral</p>
        <p className="mt-1">© 2025 GW2 Optimizer - Tous droits réservés</p>
      </div>
    </div>
  );
};
