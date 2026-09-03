/**
 * Re-exportação unificada de todos os serviços e tipos da API.
 */
import { projectsApi } from './projects';
import { templatesApi } from './templates';
import { batchesApi } from './batches';
import { automationApi } from './automation';
import { filtersApi } from './filters';
import { profileApi } from './profile';
import { dashboardApi } from './dashboard';

export * from './client';
export * from './projects';
export * from './templates';
export * from './batches';
export * from './automation';
export * from './filters';
export * from './profile';
export * from './dashboard';

export const api = {
    ...projectsApi,
    ...templatesApi,
    ...batchesApi,
    ...automationApi,
    ...filtersApi,
    ...profileApi,
    ...dashboardApi,
};

export default api;
