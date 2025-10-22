/**
 * Sentry Test Button Component
 * 
 * This component is used to test Sentry error tracking in the frontend.
 * It should only be visible in development mode.
 */

import * as Sentry from '@sentry/react';

export function SentryTestButton() {
  // Only show in development
  if (import.meta.env.PROD) {
    return null;
  }

  const handleClick = () => {
    // Send a log before throwing the error
    Sentry.captureMessage('User triggered test error', {
      level: 'info',
      tags: {
        action: 'test_error_button_click',
      },
    });

    // Throw test error
    throw new Error('This is your first Sentry error! 🎉');
  };

  return (
    <button
      onClick={handleClick}
      className="fixed bottom-4 right-4 px-4 py-2 bg-red-500 text-white rounded-lg shadow-lg hover:bg-red-600 transition-colors"
      title="Test Sentry Error Tracking"
    >
      🐛 Test Sentry
    </button>
  );
}
