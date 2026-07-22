import { createBrowserRouter, Navigate } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import { Dashboard } from './pages/Dashboard';
import { ProjectOverview } from './pages/ProjectOverview';
import { CollectLeads } from './pages/CollectLeads';
import { ReviewLeads } from './pages/ReviewLeads';
import { Enrichments } from './pages/Enrichments';
import { ReviewEnrichment } from './pages/ReviewEnrichment';
import { TestEnrichment } from './pages/TestEnrichment';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppShell />,
    children: [
      { index: true, element: <Dashboard /> },
      { path: 'projects/:projectId', element: <ProjectOverview /> },
      { path: 'projects/:projectId/collect', element: <CollectLeads /> },
      { path: 'projects/:projectId/review', element: <ReviewLeads /> },
      { path: 'projects/:projectId/enrichments', element: <Enrichments /> },
      {
        path: 'projects/:projectId/enrichments/:enrichmentId/review',
        element: <ReviewEnrichment />,
      },
      {
        path: 'projects/:projectId/enrichments/:enrichmentId/test',
        element: <TestEnrichment />,
      },
      { path: '*', element: <Navigate to="/" replace /> },
    ],
  },
]);
