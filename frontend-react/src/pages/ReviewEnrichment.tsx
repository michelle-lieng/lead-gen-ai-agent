import { Alert, Box, Button, Card, CardContent, Typography } from '@mui/material';
import ScienceIcon from '@mui/icons-material/Science';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { enrichLeads } from '../api/enrichments';
import { getMergedResults } from '../api/mergedResults';
import { EnrichLeadsResponse, LeadRow } from '../api/types';
import { useApiKeysDialog } from '../components/apiKeys/ApiKeysProvider';
import { LoadingButton } from '../components/common/LoadingButton';
import { useNotify } from '../components/common/Notifications';
import { PageHeader } from '../components/common/PageHeader';
import {
  configFromEnrichment,
  EnrichmentConfigFields,
  validateConfig,
} from '../components/enrichments/EnrichmentConfigFields';
import { EnrichedResultsGrid } from '../components/enrichments/EnrichedResultsGrid';
import { useEnrichment } from '../hooks/useEnrichments';
import { queryKeys } from '../hooks/queryKeys';

export function ReviewEnrichment() {
  const { projectId, enrichmentId } = useParams();
  const projId = Number(projectId);
  const enrId = Number(enrichmentId);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { notify, notifyError } = useNotify();
  const { requireKeys } = useApiKeysDialog();
  const { data: enrichment, isLoading } = useEnrichment(enrId);
  const [result, setResult] = useState<EnrichLeadsResponse | null>(null);

  const config = useMemo(
    () => (enrichment ? configFromEnrichment(enrichment) : null),
    [enrichment],
  );

  const runMutation = useMutation({
    mutationFn: async () => {
      const merged = await getMergedResults(projId);
      if (!merged.data || merged.data.length === 0) {
        throw new Error('No leads to enrich. Collect leads or upload a dataset first.');
      }
      return enrichLeads(projId, enrId, merged.data as LeadRow[]);
    },
    onSuccess: (data) => {
      setResult(data);
      if (data.enriched_leads.length === 0) {
        notify('All leads were already enriched for this column.', 'info');
      } else {
        notify(
          `Enrichment completed on ${data.leads_processed} lead(s). Saved to merged leads.`,
          'success',
        );
      }
      queryClient.invalidateQueries({ queryKey: queryKeys.mergedResults(projId) });
    },
    onError: notifyError,
  });

  const handleRun = () => {
    if (!config) return;
    const missing = validateConfig(config);
    if (missing.length > 0) {
      notify(`Please complete the config first: ${missing.join(', ')}.`, 'warning');
      return;
    }
    if (!requireKeys()) return;
    setResult(null);
    runMutation.mutate();
  };

  if (isLoading) return <Typography color="text.secondary">Loading enrichment...</Typography>;
  if (!enrichment || !config)
    return <Typography color="error">No enrichment selected.</Typography>;

  return (
    <Box>
      <PageHeader
        title={`Run Enrichment — ${enrichment.enrichment_name}`}
        actions={
          <Button
            variant="outlined"
            startIcon={<ScienceIcon />}
            onClick={() => navigate(`/projects/${projId}/enrichments/${enrId}/test`)}
          >
            Go to Test Page
          </Button>
        }
      />

      <Alert severity="info" sx={{ mb: 2 }}>
        This page is read-only. To change these fields, use the Test page.
      </Alert>

      <Card variant="outlined" sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Enrichment Configuration
          </Typography>
          <EnrichmentConfigFields config={config} disabled />
        </CardContent>
      </Card>

      <LoadingButton
        variant="contained"
        startIcon={<PlayArrowIcon />}
        loading={runMutation.isPending}
        onClick={handleRun}
      >
        Run Enrichment on All Leads
      </LoadingButton>
      {runMutation.isPending && (
        <Alert severity="warning" sx={{ mt: 2 }}>
          Running enrichment on all leads — this can take several minutes. Please don't
          navigate away.
        </Alert>
      )}

      {result && result.enriched_leads.length > 0 && (
        <Box sx={{ mt: 3 }}>
          <Typography variant="h6" gutterBottom>
            Results ({result.leads_processed} lead(s))
          </Typography>
          <EnrichedResultsGrid columns={result.columns} rows={result.enriched_leads} />
        </Box>
      )}
    </Box>
  );
}
