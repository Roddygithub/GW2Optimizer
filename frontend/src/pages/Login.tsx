import { useState, type FormEvent } from 'react';
import { login } from '../services/auth';
import { useAuthStore } from '../store/auth';
import { navigate } from '@/lib/navigation';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const setUser = useAuthStore((state) => state.setUser);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (isSubmitting) return;

    setIsSubmitting(true);
    setMessage(null);

    try {
      const response = await login(email, password);

      if (response?.user) {
        setUser(response.user);
        navigate('/builds');
        return;
      }

      setMessage('Login succeeded but no user information was returned.');
    } catch (error) {
      console.error('Login failed', error);
      setMessage('Invalid credentials');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="mx-auto max-w-md space-y-4 p-4">
      <h1 className="text-2xl font-semibold">Login</h1>
      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="space-y-1">
          <label htmlFor="login-email" className="block text-sm font-medium">
            Email
          </label>
          <input
            id="login-email"
            data-testid="email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            className="w-full rounded border border-border px-3 py-2"
            placeholder="Email"
            required
          />
        </div>
        <div className="space-y-1">
          <label htmlFor="login-password" className="block text-sm font-medium">
            Password
          </label>
          <input
            id="login-password"
            data-testid="password"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="w-full rounded border border-border px-3 py-2"
            placeholder="Password"
            required
          />
        </div>
        <button
          data-testid="submit"
          type="submit"
          className="w-full rounded bg-blue-600 px-3 py-2 text-white disabled:opacity-70"
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Logging in…' : 'Login'}
        </button>
      </form>
      {message && <p className="text-sm text-red-600" data-testid="feedback">{message}</p>}
    </div>
  );
}
