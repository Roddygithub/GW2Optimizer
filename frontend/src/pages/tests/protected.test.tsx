import '@testing-library/jest-dom/vitest';
import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import ProtectedRoute from '../../components/ProtectedRoute';
import { useAuthStore } from '../../store/auth';

const ProtectedContent = () => <div data-testid="protected">Protected</div>;

const LoginFallback = () => <div data-testid="login">Login</div>;

describe('ProtectedRoute', () => {
  beforeEach(() => {
    useAuthStore.setState({ user: null });
  });

  it('redirects to /login when user is not authenticated', () => {
    render(
      <MemoryRouter initialEntries={['/teams']}>
        <Routes>
          <Route
            path="/teams"
            element={
              <ProtectedRoute>
                <ProtectedContent />
              </ProtectedRoute>
            }
          />
          <Route path="/login" element={<LoginFallback />} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByTestId('login')).toBeInTheDocument();
  });

  it('renders children when user is authenticated', () => {
    useAuthStore.setState({ user: { id: '1', email: 'user@example.com' } });

    render(
      <MemoryRouter initialEntries={['/teams']}>
        <Routes>
          <Route
            path="/teams"
            element={
              <ProtectedRoute>
                <ProtectedContent />
              </ProtectedRoute>
            }
          />
          <Route path="/login" element={<LoginFallback />} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByTestId('protected')).toBeInTheDocument();
  });
});
