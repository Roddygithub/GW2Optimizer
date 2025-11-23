import React from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { authService } from '../services/auth.service';

const Layout: React.FC = () => {
  const navigate = useNavigate();

  const handleLogout = () => {
    authService.logout();
    navigate('/login', { replace: true });
  };

  const navLinkClasses = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
      isActive
        ? 'bg-indigo-600 text-white'
        : 'text-slate-300 hover:bg-slate-800 hover:text-white'
    }`;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 flex">
      <aside className="w-64 border-r border-slate-800 bg-slate-950/80 backdrop-blur flex flex-col">
        <div className="px-6 py-4 border-b border-slate-800">
          <h1 className="text-lg font-semibold tracking-tight text-white">GW2 Optimizer</h1>
          <p className="text-xs text-slate-400 mt-1">AI Dashboard</p>
        </div>
        <nav className="px-3 py-4 space-y-1 flex-1">
          <NavLink to="/" end className={navLinkClasses}>
            <span className="h-2 w-2 rounded-full bg-indigo-500" />
            <span>Dashboard</span>
          </NavLink>
          <NavLink to="/ai-lab" className={navLinkClasses}>
            <span className="h-2 w-2 rounded-full bg-indigo-500" />
            <span>AI Lab</span>
          </NavLink>
          <NavLink to="/ai-build-lab" className={navLinkClasses}>
            <span className="h-2 w-2 rounded-full bg-emerald-500" />
            <span>Build Lab</span>
          </NavLink>
        </nav>
        <div className="mt-auto px-3 py-4 border-t border-slate-800">
          <button
            type="button"
            onClick={handleLogout}
            className="w-full inline-flex items-center justify-center rounded-md bg-slate-800 hover:bg-slate-700 px-3 py-2 text-xs font-medium text-slate-200 border border-slate-700"
          >
            Déconnexion
          </button>
        </div>
      </aside>
      <div className="flex-1 flex flex-col min-h-screen">
        <header className="h-14 border-b border-slate-800 flex items-center justify-between px-6 bg-slate-950/60 backdrop-blur">
          <div className="text-sm text-slate-400">Tableau de bord GW2 Optimizer</div>
        </header>
        <main className="flex-1 p-6 bg-gradient-to-b from-slate-950 to-slate-900">
          <div className="max-w-5xl mx-auto">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};

export default Layout;
