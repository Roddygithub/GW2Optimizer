import { useState, type FormEvent } from 'react';
import { reset } from '@/services/auth';

export default function ResetPage() {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (isSubmitting) return;

    setIsSubmitting(true);
    setMessage(null);

    try {
      await reset(email);
      setMessage('Check your inbox');
    } catch (error) {
      console.error('Reset failed', error);
      setMessage('Reset failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="mx-auto max-w-md space-y-4 p-4">
      <h1 className="text-2xl font-semibold">Reset Password</h1>
      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="space-y-1">
          <label htmlFor="reset-email" className="block text-sm font-medium">
            Email
          </label>
          <input
            id="reset-email"
            data-testid="email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            className="w-full rounded border border-border px-3 py-2"
            placeholder="Email"
            required
          />
        </div>
        <button
          data-testid="submit"
          type="submit"
          className="w-full rounded bg-blue-600 px-3 py-2 text-white disabled:opacity-70"
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Sending…' : 'Reset'}
        </button>
      </form>
      {message && <p className="text-sm" data-testid="feedback">{message}</p>}
    </div>
  );
}
