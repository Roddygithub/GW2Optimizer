#!/usr/bin/env node

/**
 * Script CLI pour afficher la version de GW2Optimizer
 * Usage: npm run version
 */

const fs = require('fs');
const path = require('path');

// Couleurs pour le terminal
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  cyan: '\x1b[36m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
};

function readPackageJson() {
  const packagePath = path.join(__dirname, '..', 'package.json');
  try {
    const packageJson = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
    return packageJson;
  } catch (error) {
    console.error(`${colors.red}❌ Erreur lors de la lecture de package.json:${colors.reset}`, error.message);
    process.exit(1);
  }
}

function readVersionConfig() {
  const versionPath = path.join(__dirname, '..', 'src', 'config', 'version.ts');
  try {
    const content = fs.readFileSync(versionPath, 'utf8');
    const versionMatch = content.match(/APP_VERSION\s*=\s*['"]([^'"]+)['"]/);
    const nameMatch = content.match(/APP_NAME\s*=\s*['"]([^'"]+)['"]/);
    const subtitleMatch = content.match(/APP_SUBTITLE\s*=\s*['"]([^'"]+)['"]/);
    
    return {
      version: versionMatch ? versionMatch[1] : null,
      name: nameMatch ? nameMatch[1] : null,
      subtitle: subtitleMatch ? subtitleMatch[1] : null,
    };
  } catch (error) {
    return { version: null, name: null, subtitle: null };
  }
}

function displayVersion() {
  const pkg = readPackageJson();
  const versionConfig = readVersionConfig();
  
  console.log('\n' + '='.repeat(60));
  console.log(`${colors.bright}${colors.cyan}🎮 GW2 Optimizer - Informations de Version${colors.reset}`);
  console.log('='.repeat(60) + '\n');
  
  // Version principale
  console.log(`${colors.green}📦 Package Version:${colors.reset}     ${colors.bright}v${pkg.version}${colors.reset}`);
  
  // Version depuis config
  if (versionConfig.version) {
    console.log(`${colors.green}⚙️  Config Version:${colors.reset}      ${colors.bright}v${versionConfig.version}${colors.reset}`);
  }
  
  // Nom de l'application
  if (versionConfig.name) {
    console.log(`${colors.blue}📛 Application Name:${colors.reset}    ${colors.bright}${versionConfig.name}${colors.reset}`);
  }
  
  // Sous-titre
  if (versionConfig.subtitle) {
    console.log(`${colors.blue}📝 Subtitle:${colors.reset}            ${colors.bright}${versionConfig.subtitle}${colors.reset}`);
  }
  
  // Environnement
  const nodeVersion = process.version;
  console.log(`${colors.yellow}🔧 Node Version:${colors.reset}        ${nodeVersion}`);
  
  // Date de build
  const buildDate = new Date().toLocaleString('fr-FR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
  console.log(`${colors.yellow}📅 Build Date:${colors.reset}          ${buildDate}`);
  
  console.log('\n' + '='.repeat(60));
  
  // Vérification de cohérence
  if (versionConfig.version && pkg.version !== versionConfig.version) {
    console.log(`\n${colors.yellow}⚠️  ATTENTION: Les versions ne correspondent pas !${colors.reset}`);
    console.log(`   package.json: v${pkg.version}`);
    console.log(`   version.ts:   v${versionConfig.version}`);
    console.log(`\n   Pensez à synchroniser les versions.\n`);
  } else {
    console.log(`\n${colors.green}✅ Toutes les versions sont synchronisées !${colors.reset}\n`);
  }
}

// Exécution
displayVersion();
