import { Box, Tab, Tabs, Typography } from '@mui/material';
import TravelExploreIcon from '@mui/icons-material/TravelExplore';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { PageHeader } from '../components/common/PageHeader';
import { useProject } from '../hooks/useProjects';
import { WebSearchTab } from './collect/WebSearchTab';
import { UploadDatasetTab } from './collect/UploadDatasetTab';

export function CollectLeads() {
  const { projectId } = useParams();
  const id = Number(projectId);
  const { data: project, isLoading } = useProject(id);
  const [tab, setTab] = useState(0);

  if (isLoading) return <Typography color="text.secondary">Loading project...</Typography>;
  if (!project) return <Typography color="error">No project selected.</Typography>;

  return (
    <Box>
      <PageHeader title={`Lead Collection — ${project.project_name}`} />
      <Tabs value={tab} onChange={(_e, value) => setTab(value)} sx={{ mb: 2 }}>
        <Tab icon={<TravelExploreIcon />} iconPosition="start" label="AI Web Search" />
        <Tab icon={<UploadFileIcon />} iconPosition="start" label="Upload Dataset" />
      </Tabs>
      {tab === 0 && <WebSearchTab project={project} />}
      {tab === 1 && <UploadDatasetTab projectId={id} />}
    </Box>
  );
}
