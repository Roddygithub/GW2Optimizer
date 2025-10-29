// Global type declarations for environment variables
declare namespace NodeJS {
  interface ProcessEnv {
    E2E_BASE_URL?: string;
    E2E_USER?: string;
    E2E_PASS?: string;
    CI?: string;
  }
}
