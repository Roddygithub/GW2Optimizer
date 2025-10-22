import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { Layout } from './components/layout/Layout';
import { Home } from './pages/Home';
import { Dashboard } from './pages/Dashboard';

// Placeholder pages
const Builds = () => (
  <div className="text-center py-12">
    <h1 className="text-3xl font-bold mb-4">Bibliothèque de Builds</h1>
    <p className="text-muted-foreground">Page en construction...</p>
  </div>
);

const Teams = () => (
  <div className="text-center py-12">
    <h1 className="text-3xl font-bold mb-4">Gestion d'Escouades</h1>
    <p className="text-muted-foreground">Page en construction...</p>
  </div>
);

const Stats = () => (
  <div className="text-center py-12">
    <h1 className="text-3xl font-bold mb-4">Statistiques</h1>
    <p className="text-muted-foreground">Page en construction...</p>
  </div>
);

const Profile = () => (
  <div className="text-center py-12">
    <h1 className="text-3xl font-bold mb-4">Profil</h1>
    <p className="text-muted-foreground">Page en construction...</p>
  </div>
);

const Settings = () => (
  <div className="text-center py-12">
    <h1 className="text-3xl font-bold mb-4">Paramètres</h1>
    <p className="text-muted-foreground">Page en construction...</p>
  </div>
);

const Login = () => (
  <div className="text-center py-12">
    <h1 className="text-3xl font-bold mb-4">Connexion</h1>
    <p className="text-muted-foreground">Page en construction...</p>
  </div>
);

const Register = () => (
  <div className="text-center py-12">
    <h1 className="text-3xl font-bold mb-4">Inscription</h1>
    <p className="text-muted-foreground">Page en construction...</p>
  </div>
);

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Home />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="builds" element={<Builds />} />
            <Route path="teams" element={<Teams />} />
            <Route path="stats" element={<Stats />} />
            <Route path="profile" element={<Profile />} />
            <Route path="settings" element={<Settings />} />
            <Route path="login" element={<Login />} />
            <Route path="register" element={<Register />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
