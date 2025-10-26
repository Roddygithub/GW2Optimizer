/**
 * Hook useAppVersion - Gestion de la version de l'application
 * 
 * Fournit des utilitaires pour accéder et afficher la version de l'application
 * depuis n'importe quel composant React ou depuis la console du navigateur.
 */

import { useEffect } from 'react';
import { VERSION_INFO, APP_VERSION, APP_NAME, APP_SUBTITLE } from '../config/version';

export interface AppVersionInfo {
  version: string;
  name: string;
  subtitle: string;
  fullTitle: string;
  copyright: string;
  buildDate: string;
}

/**
 * Affiche les informations de version dans la console du navigateur
 */
export const showAppVersion = (): void => {
  const styles = {
    title: 'color: #FFD700; font-size: 16px; font-weight: bold;',
    label: 'color: #4A90E2; font-weight: bold;',
    value: 'color: #2ECC71; font-weight: normal;',
    separator: 'color: #95A5A6;',
  };

  console.log('%c' + '='.repeat(60), styles.separator);
  console.log('%c🎮 GW2 Optimizer - Informations de Version', styles.title);
  console.log('%c' + '='.repeat(60), styles.separator);
  console.log('%c📦 Version:%c ' + VERSION_INFO.version, styles.label, styles.value);
  console.log('%c📛 Application:%c ' + VERSION_INFO.name, styles.label, styles.value);
  console.log('%c📝 Subtitle:%c ' + VERSION_INFO.subtitle, styles.label, styles.value);
  console.log('%c📅 Build Date:%c ' + new Date(VERSION_INFO.buildDate).toLocaleString('fr-FR'), styles.label, styles.value);
  console.log('%c©️ Copyright:%c ' + VERSION_INFO.copyright, styles.label, styles.value);
  console.log('%c' + '='.repeat(60), styles.separator);
  console.log('%c💡 Astuce: Tapez window.showAppVersion() pour réafficher ces informations', 'color: #95A5A6; font-style: italic;');
};

/**
 * Retourne les informations de version de l'application
 */
export const getAppVersion = (): AppVersionInfo => {
  return {
    version: APP_VERSION,
    name: APP_NAME,
    subtitle: APP_SUBTITLE,
    fullTitle: VERSION_INFO.fullTitle,
    copyright: VERSION_INFO.copyright,
    buildDate: VERSION_INFO.buildDate,
  };
};

/**
 * Hook React pour gérer la version de l'application
 * 
 * @param options Configuration du hook
 * @param options.logOnMount Si true, affiche la version dans la console au montage du composant
 * @returns Informations de version et fonction d'affichage
 * 
 * @example
 * ```tsx
 * const { version, showVersion } = useAppVersion({ logOnMount: true });
 * 
 * return (
 *   <div>
 *     <p>Version: {version}</p>
 *     <button onClick={showVersion}>Afficher la version</button>
 *   </div>
 * );
 * ```
 */
export const useAppVersion = (options: { logOnMount?: boolean } = {}) => {
  const { logOnMount = false } = options;

  useEffect(() => {
    if (logOnMount) {
      showAppVersion();
    }
  }, [logOnMount]);

  return {
    ...getAppVersion(),
    showVersion: showAppVersion,
  };
};

/**
 * Expose la fonction showAppVersion globalement dans window
 * À appeler dans le point d'entrée de l'application (main.tsx)
 */
export const exposeVersionToWindow = (): void => {
  if (typeof window !== 'undefined') {
    const w = window as unknown as {
      showAppVersion?: () => void;
      getAppVersion?: () => AppVersionInfo;
    };
    w.showAppVersion = showAppVersion;
    w.getAppVersion = getAppVersion;
    
    // Affiche un message de bienvenue avec la version
    console.log(
      '%c🚀 GW2 Optimizer %cv' + APP_VERSION,
      'color: #FFD700; font-size: 18px; font-weight: bold;',
      'color: #2ECC71; font-size: 18px; font-weight: bold;'
    );
    console.log(
      '%c💡 Tapez %cwindow.showAppVersion()%c pour afficher les détails de version',
      'color: #95A5A6;',
      'color: #4A90E2; font-weight: bold; background: #f0f0f0; padding: 2px 4px; border-radius: 3px;',
      'color: #95A5A6;'
    );
  }
};

export default useAppVersion;
