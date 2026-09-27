import { createBrowserRouter, Navigate, useParams } from 'react-router-dom';
import { Projects } from './pages/Projects';
import { Project } from './pages/Project';

/**
 * Two surfaces, and nothing else: the shelf of registers, and one register.
 * The old step-by-step routes (collect / enrichments / review) were replaced
 * by the enquiry desk on the project page.
 */
export const router = createBrowserRouter([
  { path: '/', element: <Projects /> },
  { path: '/projects/:projectId', element: <ProjectRoute /> },
  { path: '*', element: <Navigate to="/" replace /> },
]);

/**
 * One page instance per project. Without the key, moving between projects
 * reuses the page, and the previous project's run and conversation stay on
 * screen under the next project's name.
 */
function ProjectRoute() {
  const { projectId } = useParams();
  return <Project key={projectId} />;
}
