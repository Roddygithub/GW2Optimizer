import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { Home } from './pages/Home';
import LoginPage from './pages/Login';
import RegisterPage from './pages/Register';
import ResetPage from './pages/Reset';
import BuildsPage from './pages/Builds';
import TeamsPage from './pages/Teams';
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  return (
    <BrowserRouter>
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
    </BrowserRouter>
  );
}

export default App;
