import { BrowserRouter as Router, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';

// A simple hook to check auth status (e.g., by checking for a cookie or a token in local storage)
const useAuth = () => {
  // In a real app, you'd have more robust logic here.
  // For now, we can assume if the cookie is set, the user is "potentially" logged in.
  // The backend will validate the token on each request.
  const hasAuthCookie = document.cookie.includes('access_token=');
  return hasAuthCookie;
};

const ProtectedRoute = () => {
  const isAuth = useAuth();
  return isAuth ? <Outlet /> : <Navigate to="/login" />;
};

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/" element={<ProtectedRoute />}>
          <Route path="/dashboard" element={<DashboardPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/login" />} />
      </Routes>
    </Router>
  );
}

export default App;