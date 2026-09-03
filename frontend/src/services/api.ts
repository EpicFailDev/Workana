/**
 * Fachada central de serviços de API.
 * Re-exporta serviços modulares de `./api` para manter compatibilidade e organização (Clean Code & SRP).
 */
export * from './api/index';
export { api, default } from './api/index';
