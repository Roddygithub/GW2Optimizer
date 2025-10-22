import { useEffect, useState } from 'react';
import { Users, Sword, TrendingUp, Shield } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { teamsAPI, buildsAPI } from '../services/api';
import type { TeamComposition, Build } from '../types';

export const Dashboard = () => {
  const [teams, setTeams] = useState<TeamComposition[]>([]);
  const [builds, setBuilds] = useState<Build[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [teamsData, buildsData] = await Promise.all([
          teamsAPI.list({ limit: 5 }),
          buildsAPI.list({ limit: 10 }),
        ]);
        setTeams(teamsData);
        setBuilds(buildsData);
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gw2-gold"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold text-gw2-gold mb-2">
          Dashboard McM WvW
        </h1>
        <p className="text-muted-foreground">
          Gestion d'escouades et optimisation de compositions
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-profession-guardian/20 to-transparent border-profession-guardian/30">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Escouades Actives</CardTitle>
            <Users className="h-4 w-4 text-profession-guardian" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-profession-guardian">{teams.length}</div>
            <p className="text-xs text-muted-foreground">+2 cette semaine</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-profession-warrior/20 to-transparent border-profession-warrior/30">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Builds Disponibles</CardTitle>
            <Sword className="h-4 w-4 text-profession-warrior" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-profession-warrior">{builds.length}</div>
            <p className="text-xs text-muted-foreground">+5 ce mois-ci</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-gw2-gold/20 to-transparent border-gw2-gold/30">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Taux de Victoire</CardTitle>
            <TrendingUp className="h-4 w-4 text-gw2-gold" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gw2-gold">68%</div>
            <p className="text-xs text-muted-foreground">+12% vs mois dernier</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-profession-mesmer/20 to-transparent border-profession-mesmer/30">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Synergies Optimales</CardTitle>
            <Shield className="h-4 w-4 text-profession-mesmer" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-profession-mesmer">24</div>
            <p className="text-xs text-muted-foreground">Compositions validées</p>
          </CardContent>
        </Card>
      </div>

      {/* Recent Teams */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Escouades Récentes</CardTitle>
            <CardDescription>Vos dernières compositions d'escouade</CardDescription>
          </CardHeader>
          <CardContent>
            {teams.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">
                Aucune escouade créée. Créez votre première composition !
              </p>
            ) : (
              <div className="space-y-4">
                {teams.map((team) => (
                  <div
                    key={team.id}
                    className="flex items-center justify-between p-4 rounded-lg border border-border hover:bg-accent/50 transition-colors cursor-pointer"
                  >
                    <div>
                      <h4 className="font-medium">{team.name}</h4>
                      <p className="text-sm text-muted-foreground">
                        {team.game_mode.toUpperCase()} • {team.slots?.length || 0}/{team.team_size} slots
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      {team.overall_rating && (
                        <span className="text-sm font-medium text-gw2-gold">
                          {team.overall_rating.toFixed(1)}/10
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Builds Populaires</CardTitle>
            <CardDescription>Les builds les plus utilisés en WvW</CardDescription>
          </CardHeader>
          <CardContent>
            {builds.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">
                Aucun build disponible. Créez votre premier build !
              </p>
            ) : (
              <div className="space-y-4">
                {builds.slice(0, 5).map((build) => (
                  <div
                    key={build.id}
                    className="flex items-center justify-between p-4 rounded-lg border border-border hover:bg-accent/50 transition-colors cursor-pointer"
                  >
                    <div>
                      <h4 className="font-medium">{build.name}</h4>
                      <p className="text-sm text-muted-foreground">
                        {build.profession} • {build.role}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span
                        className="w-3 h-3 rounded-full"
                        style={{
                          backgroundColor: getProfessionColor(build.profession),
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

function getProfessionColor(profession: string): string {
  const colors: Record<string, string> = {
    Guardian: '#72C1D9',
    Warrior: '#FFD166',
    Engineer: '#D09C59',
    Ranger: '#8CDC82',
    Thief: '#C08F95',
    Elementalist: '#F68A87',
    Mesmer: '#B679D5',
    Necromancer: '#52A76F',
    Revenant: '#D16E5A',
  };
  return colors[profession] || '#888';
}
