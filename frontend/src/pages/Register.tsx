import { useState, type FormEvent } from 'react';
import { register } from '../services/auth';
import { navigate } from '@/lib/navigation';

export default function RegisterPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (isSubmitting) return;

    setIsSubmitting(true);
    setMessage(null);

    try {
      await register(email, password);
      setMessage('Registered. Please login.');
      navigate('/login');
    } catch (error) {
      console.error('Registration failed', error);
      setMessage('Registration failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="mx-auto max-w-md space-y-4 p-4">
      <h1 className="text-2xl font-semibold">Register</h1>
      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="space-y-1">
          <label htmlFor="register-email" className="block text-sm font-medium">
            Email
          </label>
          <input
            id="register-email"
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
          <label htmlFor="register-password" className="block text-sm font-medium">
            Password
          </label>
          <input
            id="register-password"
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
          {isSubmitting ? 'Registering…' : 'Register'}
        </button>
      </form>
      {message && <p className="text-sm" data-testid="feedback">{message}</p>}
    </div>
  );
}
