import { createRouter, createWebHistory } from 'vue-router';
import AdminView from './views/AdminView.vue';
import PortalView from './views/PortalView.vue';

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/admin', name: 'admin', component: AdminView },
    { path: '/', redirect: '/home' },
    { path: '/:pageKey', name: 'portal-page', component: PortalView }
  ]
});
