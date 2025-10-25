import { Link } from 'react-router-dom';
import { Shield, Bot } from 'lucide-react';
import { APP_NAME, APP_VERSION, APP_SUBTITLE } from '../../config/version';

export const Navbar = () => {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-card/95 backdrop-blur-sm border-b border-border">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Left: Logo */}
          <div className="flex items-center gap-4">
            <Link to="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
              <Shield className="h-8 w-8 text-gw2-gold" />
              <div className="flex flex-col">
                <span className="text-xl font-bold text-gw2-gold">{APP_NAME}</span>
                <span className="text-xs text-muted-foreground">{APP_SUBTITLE}</span>
              </div>
            </Link>
          </div>

          {/* Center: AI Badge */}
          <div className="hidden md:flex items-center gap-2 px-4 py-2 rounded-full bg-gw2-gold/10 border border-gw2-gold/30">
            <Bot className="h-4 w-4 text-gw2-gold" />
            <span className="text-sm text-gw2-gold font-medium">Assistant IA Mistral</span>
          </div>

          {/* Right: Version */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">v{APP_VERSION}</span>
          </div>
        </div>
      </div>

    </nav>
  );
};
