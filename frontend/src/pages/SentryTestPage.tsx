import React, { useEffect, useState } from 'react';

const SentryTestPage: React.FC = () => {
  const [shouldCrash, setShouldCrash] = useState(false);

  useEffect(() => {
    if (shouldCrash) {
      // This will be captured by Sentry's ErrorBoundary
      throw new Error('Sentry Frontend Test Error');
    }
  }, [shouldCrash]);

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center bg-slate-950 text-slate-200">
      <div className="max-w-md w-full space-y-4 text-center border border-slate-800 bg-slate-900/70 rounded-xl p-6 shadow-xl">
        <h1 className="text-lg font-semibold">Sentry Frontend - Crash Test</h1>
        <p className="text-sm text-slate-400">
          Cette page est cachée et sert uniquement à vérifier que les erreurs React sont bien remontées dans Sentry.
        </p>
        <button
          type="button"
          onClick={() => setShouldCrash(true)}
          className="inline-flex items-center justify-center rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white shadow hover:bg-red-500 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 focus:ring-offset-slate-900"
        >
          Provoquer une erreur Sentry
        </button>
        <p className="text-xs text-slate-500">
          Après le crash, vérifie dans ton projet Sentry qu&apos;un nouvel event &laquo; Sentry Frontend Test Error &raquo; est apparu.
        </p>
      </div>
    </div>
  );
};

export default SentryTestPage;
