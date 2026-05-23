import { createRouter, createWebHistory } from 'vue-router';
import AdminView from './views/AdminView.vue';
import AuthView from './views/AuthView.vue';
import AudioPage from './components/AudioPage.vue';
import CourseLibraryPage from './components/CourseLibraryPage.vue';
import ImagePage from './components/ImagePage.vue';
import MembershipBenefitsPage from './components/MembershipBenefitsPage.vue';
import PortalDetailPage from './components/PortalDetailPage.vue';
import VideoPage from './components/VideoPage.vue';
import WorkbenchPage from './components/WorkbenchPage.vue';
import PortalView from './views/PortalView.vue';

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/admin', name: 'admin', component: AdminView },
    { path: '/auth', name: 'auth', component: AuthView },
    { path: '/workbench', name: 'workbench', component: WorkbenchPage },
    { path: '/workbench/image', name: 'workbench-image', component: ImagePage },
    { path: '/workbench/video', name: 'workbench-video', component: VideoPage },
    { path: '/workbench/audio', name: 'workbench-audio', component: AudioPage },
    { path: '/', redirect: '/home' },
    { path: '/membership/benefits', name: 'membership-benefits', component: MembershipBenefitsPage },
    { path: '/learning', name: 'course-library', component: CourseLibraryPage },
    { path: '/workspace/:detailPath(.*)*', name: 'portal-detail-workspace', component: PortalDetailPage },
    { path: '/community/:detailPath(.*)*', name: 'portal-detail-community', component: PortalDetailPage },
    { path: '/templates/:detailPath(.*)*', name: 'portal-detail-templates', component: PortalDetailPage },
    { path: '/templates', name: 'portal-detail-template-root', component: PortalDetailPage },
    { path: '/resources/:detailPath(.*)*', name: 'portal-detail-resources', component: PortalDetailPage },
    { path: '/resources', name: 'portal-detail-resource-root', component: PortalDetailPage },
    { path: '/projects/:detailPath(.*)*', name: 'portal-detail-projects', component: PortalDetailPage },
    { path: '/toolkit/:detailPath(.*)*', name: 'portal-detail-toolkit', component: PortalDetailPage },
    { path: '/learning/:detailPath(.*)*', name: 'portal-detail-learning', component: PortalDetailPage },
    { path: '/:pageKey', name: 'portal-page', component: PortalView },
    { path: '/:detailPath(.*)*', name: 'portal-detail', component: PortalDetailPage }
  ]
});
