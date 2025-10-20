import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import apiClient from '../services/api';

const RegisterPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [success, setSuccess] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setIsLoading(true);
    setError(null);
    setFieldErrors({});
    setSuccess(null);

    try {
      await apiClient.post('/auth/register', {
        username,
        email,
        password,
      });

      setSuccess('Registration successful! Please check your email to verify your account.');
      setTimeout(() => navigate('/login'), 3000);

    } catch (err: any) {
      if (err.response && err.response.data) {
        const responseData = err.response.data;
        if (responseData.error_code === 'VALIDATION_ERROR') {
          setError(responseData.detail);
          setFieldErrors(responseData.fields || {});
        } else {
          setError(responseData.detail || 'Registration failed. Please try again.');
        }
      } else {
        setError('An unexpected error occurred. Please try again.');
      }
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-gray-200 flex items-center justify-center p-4">
      <div className="w-full max-w-md p-8 space-y-6 bg-gray-800 rounded-lg shadow-lg">
        <h1 className="text-3xl font-bold text-center text-white">Create Account</h1>
        {success ? (
          <p className="text-center text-green-400">{success}</p>
        ) : (
          <>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label htmlFor="username" className="text-sm font-medium">Username</label>
                <input id="username" type="text" value={username} onChange={(e) => setUsername(e.target.value)} required className="w-full px-3 py-2 mt-1 text-gray-200 bg-gray-700 border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" />
                {fieldErrors.username && <p className="text-xs text-red-400 mt-1">{fieldErrors.username}</p>}
              </div>
              <div>
                <label htmlFor="email" className="text-sm font-medium">Email</label>
                <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required className="w-full px-3 py-2 mt-1 text-gray-200 bg-gray-700 border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" />
                {fieldErrors.email && <p className="text-xs text-red-400 mt-1.5">{fieldErrors.email}</p>}
              </div>
              <div>
                <label htmlFor="password" className="text-sm font-medium">Password</label>
                <input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required className="w-full px-3 py-2 mt-1 text-gray-200 bg-gray-700 border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" />
                {fieldErrors.password && <p className="text-xs text-red-400 mt-1">{fieldErrors.password}</p>}
              </div>
              <div>
                <label htmlFor="confirmPassword" className="text-sm font-medium">Confirm Password</label>
                <input id="confirmPassword" type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required className="w-full px-3 py-2 mt-1 text-gray-200 bg-gray-700 border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              {error && !Object.keys(fieldErrors).length && <p className="text-sm text-red-400">{error}</p>}
              <button type="submit" disabled={isLoading} className="w-full px-4 py-2 font-bold text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-500">
                {isLoading ? 'Registering...' : 'Register'}
              </button>
            </form>
            <p className="text-sm text-center text-gray-400">
              Already have an account? <Link to="/login" className="font-medium text-blue-400 hover:underline">Login here</Link>
            </p>
          </>
        )}
      </div>
    </div>
  );
};

export default RegisterPage;