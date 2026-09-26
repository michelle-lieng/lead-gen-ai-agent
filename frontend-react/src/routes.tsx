import { createBrowserRouter, Navigate } from 'react-router-dom';
import { Projects } from './pages/Projects';
import { Project } from './pages/Project';

/**
 * Two surfaces, and nothing else: the shelf of registers, and one register.
 * The old step-by-step routes (collect / enrichments / review) were replaced
 * by the enquiry desk on the project page.
 */
export const router = createBrowserRouter([
  { path: '/', element: <Projects /> },
  { path: '/projects/:projectId', element: <Project /> },
  { path: '*', element: <Navigate to="/" replace /> },
]);
