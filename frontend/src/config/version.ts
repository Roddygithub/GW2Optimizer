/**
 * Configuration de Version - GW2 Optimizer
 * 
 * Centralise toutes les informations de version de l'application.
 */

export const APP_VERSION = '4.1.0';
export const APP_NAME = 'GW2 Optimizer';
export const APP_SUBTITLE = 'WvW McM Dashboard';
export const APP_FULL_TITLE = `${APP_NAME} v${APP_VERSION} - ${APP_SUBTITLE}`;
export const APP_COPYRIGHT = '© 2025 - WvW McM Dashboard';

export const VERSION_INFO = {
  version: APP_VERSION,
  name: APP_NAME,
  subtitle: APP_SUBTITLE,
  fullTitle: APP_FULL_TITLE,
  copyright: APP_COPYRIGHT,
  buildDate: new Date().toISOString(),
} as const;

export default VERSION_INFO;
