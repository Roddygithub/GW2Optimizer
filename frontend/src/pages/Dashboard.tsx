import React from 'react';

const Dashboard: React.FC = () => {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold text-white">Dashboard</h1>
      <p className="text-sm text-slate-400">
        Bienvenue dans le tableau de bord GW2 Optimizer. Utilisez la navigation à gauche pour accéder au laboratoire IA.
      </p>
      <div className="mt-4 grid gap-4 md:grid-cols-3">
        <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-4">
          <p className="text-xs uppercase tracking-wide text-slate-400 mb-1">Statut</p>
          <p className="text-sm text-slate-200">Backend en ligne (FastAPI)</p>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-4">
          <p className="text-xs uppercase tracking-wide text-slate-400 mb-1">IA</p>
          <p className="text-sm text-slate-200">Ollama + Mistral prêts pour l'analyse de compétences</p>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-4">
          <p className="text-xs uppercase tracking-wide text-slate-400 mb-1">Prochaine étape</p>
          <p className="text-sm text-slate-200">Testez l'analyse de skill via l'onglet "AI Lab".</p>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
