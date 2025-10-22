import { Link, useLocation } from 'react-router-dom';
import { Home, Users, Sword, BarChart3, Settings, X } from 'lucide-react';
import { cn } from '../../utils/cn';
import { Button } from '../ui/button';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

const navigation = [
  { name: 'Accueil', href: '/', icon: Home },
  { name: 'Dashboard', href: '/dashboard', icon: BarChart3 },
  { name: 'Escouades', href: '/teams', icon: Users },
  { name: 'Builds', href: '/builds', icon: Sword },
  { name: 'Paramètres', href: '/settings', icon: Settings },
];

export const Sidebar = ({ isOpen, onClose }: SidebarProps) => {
  const location = useLocation();

  return (
    <>
      {/* Mobile Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed top-16 left-0 bottom-0 w-64 bg-card border-r border-border z-40 transition-transform duration-300 lg:translate-x-0",
          isOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {/* Close button (mobile only) */}
        <div className="lg:hidden absolute top-4 right-4">
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-5 w-5" />
          </Button>
        </div>

        {/* Navigation */}
        <nav className="p-4 space-y-2">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href;
            return (
              <Link
                key={item.name}
                to={item.href}
                onClick={onClose}
                className={cn(
                  "flex items-center gap-3 px-4 py-3 rounded-lg transition-colors",
                  isActive
                    ? "bg-gw2-gold/20 text-gw2-gold font-medium"
                    : "text-foreground/70 hover:bg-accent hover:text-foreground"
                )}
              >
                <item.icon className="h-5 w-5" />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="absolute bottom-4 left-4 right-4 p-4 bg-accent/50 rounded-lg">
          <p className="text-xs text-muted-foreground text-center">
            GW2 Optimizer v1.7.0
          </p>
          <p className="text-[10px] text-muted-foreground/70 text-center mt-1">
            © 2025 - WvW McM Dashboard
          </p>
        </div>
      </aside>
    </>
  );
};
