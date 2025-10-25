import { Outlet } from 'react-router-dom';
import { Navbar } from './Navbar';

export const Layout = () => {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      <main className="pt-16 min-h-screen">
        <div className="container mx-auto p-4">
          <Outlet />
        </div>
      </main>
    </div>
  );
};
