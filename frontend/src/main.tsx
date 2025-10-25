import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import * as Sentry from "@sentry/react";
import './index.css'
import App from './App.tsx'
import { exposeVersionToWindow } from './hooks/useAppVersion'

// Expose version utilities to window and display welcome message
exposeVersionToWindow();

// Initialize Sentry (production only)
if (import.meta.env.PROD && import.meta.env.VITE_SENTRY_DSN) {
  Sentry.init({
    dsn: import.meta.env.VITE_SENTRY_DSN,
    // Integrations
    integrations: [
      Sentry.browserTracingIntegration(),
      Sentry.replayIntegration(),
    ],
    // Performance monitoring
    tracesSampleRate: 1.0,  // Capture 100% of transactions
    tracePropagationTargets: ["localhost", /^https:\/\/api\.gw2optimizer\.com/],
    // Session Replay
    replaysSessionSampleRate: 0.1,  // 10% of sessions
    replaysOnErrorSampleRate: 1.0,  // 100% of errors
    // Data collection
    sendDefaultPii: true,  // Include IP addresses
    // Environment
    environment: import.meta.env.MODE,
  });
  console.log("📊 Sentry error tracking initialized (tracing + replay + logs enabled)");
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
