import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import AiLab from './pages/AiLab';
import AiBuildLab from './pages/AiBuildLab';
import AiUrlImport from './pages/AiUrlImport';
import MyBuilds from './pages/MyBuilds';
import TeamCommander from './pages/TeamCommander';
import MetaDashboard from './pages/MetaDashboard';
import Layout from './layouts/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import SentryTestPage from './pages/SentryTestPage';

const App: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-200">
      <Routes>
        <Route path="/login" element={<Login />} />

        <Route
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route path="/" element={<Dashboard />} />
          <Route path="/meta" element={<MetaDashboard />} />
          <Route path="/ai-lab" element={<AiLab />} />
          <Route path="/ai-build-lab" element={<AiBuildLab />} />
          <Route path="/ai-url-import" element={<AiUrlImport />} />
          <Route path="/team-commander" element={<TeamCommander />} />
          <Route path="/my-builds" element={<MyBuilds />} />
          <Route path="/__sentry-test" element={<SentryTestPage />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  );
};

export default App;
