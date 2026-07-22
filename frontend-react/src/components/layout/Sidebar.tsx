import {
  Box,
  Divider,
  Drawer,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
} from '@mui/material';
import DashboardIcon from '@mui/icons-material/Dashboard';
import FolderIcon from '@mui/icons-material/Folder';
import DescriptionIcon from '@mui/icons-material/Description';
import TravelExploreIcon from '@mui/icons-material/TravelExplore';
import FactCheckIcon from '@mui/icons-material/FactCheck';
import InsightsIcon from '@mui/icons-material/Insights';
import { useNavigate, useParams } from 'react-router-dom';
import { useProjects } from '../../hooks/useProjects';
import { DRAWER_WIDTH } from './TopBar';

export function Sidebar() {
  const navigate = useNavigate();
  const params = useParams();
  const projectId = params.projectId ? Number(params.projectId) : undefined;
  const { data: projects, isLoading } = useProjects();

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: DRAWER_WIDTH,
        flexShrink: 0,
        [`& .MuiDrawer-paper`]: { width: DRAWER_WIDTH, boxSizing: 'border-box' },
      }}
    >
      <Toolbar />
      <Box sx={{ overflow: 'auto', py: 1 }}>
        <List>
          <ListItemButton
            selected={projectId === undefined}
            onClick={() => navigate('/')}
          >
            <ListItemIcon>
              <DashboardIcon />
            </ListItemIcon>
            <ListItemText primary="Dashboard" />
          </ListItemButton>
        </List>

        <Divider />

        <Typography variant="overline" sx={{ px: 2, pt: 1, display: 'block' }}>
          Projects
        </Typography>
        <List dense>
          {isLoading && (
            <ListItemText sx={{ px: 2 }} secondary="Loading..." />
          )}
          {!isLoading && (!projects || projects.length === 0) && (
            <ListItemText sx={{ px: 2 }} secondary="No projects yet" />
          )}
          {projects?.map((project) => (
            <ListItemButton
              key={project.id}
              selected={projectId === project.id}
              onClick={() => navigate(`/projects/${project.id}`)}
            >
              <ListItemIcon>
                <FolderIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText primary={project.project_name} />
            </ListItemButton>
          ))}
        </List>

        {projectId !== undefined && (
          <>
            <Divider />
            <Typography variant="overline" sx={{ px: 2, pt: 1, display: 'block' }}>
              Project Tools
            </Typography>
            <List>
              <ListItemButton onClick={() => navigate(`/projects/${projectId}`)}>
                <ListItemIcon>
                  <InsightsIcon />
                </ListItemIcon>
                <ListItemText primary="Overview" />
              </ListItemButton>
              <ListItemButton onClick={() => navigate(`/projects/${projectId}/enrichments`)}>
                <ListItemIcon>
                  <DescriptionIcon />
                </ListItemIcon>
                <ListItemText primary="Enrichments" />
              </ListItemButton>
              <ListItemButton onClick={() => navigate(`/projects/${projectId}/collect`)}>
                <ListItemIcon>
                  <TravelExploreIcon />
                </ListItemIcon>
                <ListItemText primary="Collect Leads" />
              </ListItemButton>
              <ListItemButton onClick={() => navigate(`/projects/${projectId}/review`)}>
                <ListItemIcon>
                  <FactCheckIcon />
                </ListItemIcon>
                <ListItemText primary="Review Leads" />
              </ListItemButton>
            </List>
          </>
        )}
      </Box>
    </Drawer>
  );
}
