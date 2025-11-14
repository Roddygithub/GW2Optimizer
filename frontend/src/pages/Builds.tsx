import { useState, type FormEvent } from 'react';
import { suggestBuild, type SuggestBuildResponse } from '@/services/builds';

export default function BuildsPage() {
  const [profession, setProfession] = useState('Elementalist');
  const [role, setRole] = useState('DPS');
  const [result, setResult] = useState<SuggestBuildResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (isSubmitting) return;

    setIsSubmitting(true);
    setError(null);

    try {
      const response = await suggestBuild({ profession, role, game_mode: 'WvW' });
      setResult(response);
    } catch (err) {
      console.error('Build suggestion failed', err);
      setError('Failed to fetch build suggestion');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-4 p-4">
      <h1 className="text-2xl font-semibold">Suggest a Build</h1>
      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="space-y-1">
          <label htmlFor="build-profession" className="block text-sm font-medium">
            Profession
          </label>
          <input
            id="build-profession"
            data-testid="profession"
            value={profession}
            onChange={(event) => setProfession(event.target.value)}
            className="w-full rounded border border-border px-3 py-2"
            placeholder="Profession"
          />
        </div>
        <div className="space-y-1">
          <label htmlFor="build-role" className="block text-sm font-medium">
            Role
          </label>
          <input
            id="build-role"
            data-testid="role"
            value={role}
            onChange={(event) => setRole(event.target.value)}
            className="w-full rounded border border-border px-3 py-2"
            placeholder="Role"
          />
        </div>
        <button
          data-testid="submit"
          type="submit"
          className="rounded bg-blue-600 px-3 py-2 text-white disabled:opacity-70"
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Suggesting…' : 'Suggest'}
        </button>
      </form>

      {error && (
        <p className="text-sm text-red-600" data-testid="error">
          {error}
        </p>
      )}

      {result && (
        <pre
          data-testid="result"
          className="overflow-x-auto rounded bg-gray-100 p-4 text-sm"
        >
          {JSON.stringify(result.build, null, 2)}
        </pre>
      )}
    </div>
  );
}
