import { Link } from 'react-router-dom';
import { Shield, Menu, User, LogOut } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../ui/button';

interface NavbarProps {
  onMenuClick: () => void;
}

export const Navbar = ({ onMenuClick }: NavbarProps) => {
  const { user, logout, isAuthenticated } = useAuth();

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-card/95 backdrop-blur-sm border-b border-border">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Left: Logo + Menu */}
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={onMenuClick}
              className="lg:hidden"
            >
              <Menu className="h-5 w-5" />
            </Button>
            
            <Link to="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
              <Shield className="h-8 w-8 text-gw2-gold" />
              <div className="flex flex-col">
                <span className="text-xl font-bold text-gw2-gold">GW2 Optimizer</span>
                <span className="text-xs text-muted-foreground">WvW McM Dashboard</span>
              </div>
            </Link>
          </div>

          {/* Center: Navigation Links */}
          <div className="hidden md:flex items-center gap-6">
            <Link
              to="/dashboard"
              className="text-sm font-medium text-foreground/80 hover:text-foreground transition-colors"
            >
              Dashboard
            </Link>
            <Link
              to="/builds"
              className="text-sm font-medium text-foreground/80 hover:text-foreground transition-colors"
            >
              Builds
            </Link>
            <Link
              to="/teams"
              className="text-sm font-medium text-foreground/80 hover:text-foreground transition-colors"
            >
              Escouades
            </Link>
            <Link
              to="/stats"
              className="text-sm font-medium text-foreground/80 hover:text-foreground transition-colors"
            >
              Statistiques
            </Link>
          </div>

          {/* Right: User Menu */}
          <div className="flex items-center gap-2">
            {isAuthenticated ? (
              <>
                <Link to="/profile">
                  <Button variant="ghost" size="sm" className="gap-2">
                    <User className="h-4 w-4" />
                    <span className="hidden sm:inline">{user?.username}</span>
                  </Button>
                </Link>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={logout}
                  className="gap-2"
                >
                  <LogOut className="h-4 w-4" />
                  <span className="hidden sm:inline">Déconnexion</span>
                </Button>
              </>
            ) : (
              <>
                <Link to="/login">
                  <Button variant="ghost" size="sm">
                    Connexion
                  </Button>
                </Link>
                <Link to="/register">
                  <Button variant="gw2" size="sm">
                    Inscription
                  </Button>
                </Link>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Powered by Ollama */}
      <div className="absolute bottom-0 right-4 text-[10px] text-muted-foreground/50">
        Empowered by Ollama with Mistral
      </div>
    </nav>
  );
};
