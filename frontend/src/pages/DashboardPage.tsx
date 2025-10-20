import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../services/api';
import AIRecommender from '../components/AIRecommender';
import TeamAnalyzer from '../components/TeamAnalyzer';

interface User {
  email: string;
  username: string;
  full_name?: string;
}

const DashboardPage: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const response = await apiClient.get('/auth/me');
        setUser(response.data);
      } catch (error) {
        console.error("Failed to fetch user data", error);
        // If fetching user fails (e.g., token invalid), redirect to login
        navigate('/login');
      } finally {
        setIsLoading(false);
      }
    };

    fetchUser();
  }, [navigate]);

  const handleLogout = async () => {
    try {
      await apiClient.post('/auth/logout');
    } catch (error) {
      console.error("Logout failed", error);
    } finally {
      // Clear cookie and redirect to login regardless of API call success
      document.cookie = "access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
      navigate('/login');
    }
  };

  if (isLoading) {
    return <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-4xl font-bold">Welcome, {user?.username || 'User'}!</h1>
        <button onClick={handleLogout} className="px-4 py-2 font-bold text-white bg-red-600 rounded-md hover:bg-red-700">Logout</button>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <AIRecommender />
        <TeamAnalyzer />
      </div>
    </div>
  );
};

export default DashboardPage;