import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { Home } from './pages/Home';
import ProtectedRoute from './components/ProtectedRoute';

// Lazy load auth pages (not needed on initial load)
const LoginPage = lazy(() => import('./pages/Login'));
const RegisterPage = lazy(() => import('./pages/Register'));
const ResetPage = lazy(() => import('./pages/Reset'));

// Lazy load protected pages (only for authenticated users)
const BuildsPage = lazy(() => import('./pages/Builds'));
const TeamsPage = lazy(() => import('./pages/Teams'));

// Loading fallback component
const PageLoader = () => (
  <div className="flex items-center justify-center min-h-screen">
    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
  </div>
);

function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<PageLoader />}>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Home />} />
            <Route path="login" element={<LoginPage />} />
            <Route path="register" element={<RegisterPage />} />
            <Route path="reset" element={<ResetPage />} />
            <Route
              path="builds"
              element={
                <ProtectedRoute>
                  <BuildsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="teams"
              element={
                <ProtectedRoute>
                  <TeamsPage />
                </ProtectedRoute>
              }
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}

export default App;
