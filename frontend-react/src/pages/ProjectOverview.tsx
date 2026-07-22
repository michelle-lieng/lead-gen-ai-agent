import { Box, Button, Grid, Stack, Typography } from '@mui/material';
import TravelExploreIcon from '@mui/icons-material/TravelExplore';
import DescriptionIcon from '@mui/icons-material/Description';
import FactCheckIcon from '@mui/icons-material/FactCheck';
import { useNavigate, useParams } from 'react-router-dom';
import { PageHeader } from '../components/common/PageHeader';
import { StatCard } from '../components/common/StatCard';
import { useProject } from '../hooks/useProjects';

export function ProjectOverview() {
  const { projectId } = useParams();
  const id = Number(projectId);
  const navigate = useNavigate();
  const { data: project, isLoading, isError } = useProject(id);

  if (isLoading) return <Typography color="text.secondary">Loading project...</Typography>;
  if (isError || !project) return <Typography color="error">No project selected.</Typography>;

  return (
    <Box>
      <PageHeader title={`Project Overview — ${project.project_name}`} />

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={4}>
          <StatCard label="Leads Collected" value={project.leads_collected} />
        </Grid>
        <Grid item xs={12} sm={4}>
          <StatCard label="Datasets Added" value={project.datasets_added} />
        </Grid>
        <Grid item xs={12} sm={4}>
          <StatCard label="URLs Processed" value={project.urls_processed} />
        </Grid>
      </Grid>

      {project.description && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6">Description</Typography>
          <Typography color="text.secondary">{project.description}</Typography>
        </Box>
      )}

      <Typography variant="h6" gutterBottom>
        Quick Actions
      </Typography>
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
        <Button
          variant="contained"
          startIcon={<TravelExploreIcon />}
          onClick={() => navigate(`/projects/${id}/collect`)}
        >
          Start Lead Collection
        </Button>
        <Button
          variant="outlined"
          startIcon={<DescriptionIcon />}
          onClick={() => navigate(`/projects/${id}/enrichments`)}
        >
          Start Lead Enrichment
        </Button>
        <Button
          variant="outlined"
          startIcon={<FactCheckIcon />}
          onClick={() => navigate(`/projects/${id}/review`)}
        >
          Review All Leads
        </Button>
      </Stack>
    </Box>
  );
}
