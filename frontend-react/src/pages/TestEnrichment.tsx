import { Alert, Box, Button, Card, CardContent, Typography } from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import SaveIcon from '@mui/icons-material/Save';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { testEnrichLeads, updateEnrichment } from '../api/enrichments';
import { getMergedResults } from '../api/mergedResults';
import { EnrichLeadsResponse, LeadRow } from '../api/types';
import { useApiKeysDialog } from '../components/apiKeys/ApiKeysProvider';
import { LoadingButton } from '../components/common/LoadingButton';
import { useNotify } from '../components/common/Notifications';
import { PageHeader } from '../components/common/PageHeader';
import {
  configFromEnrichment,
  EnrichmentConfig,
  EnrichmentConfigFields,
  validateConfig,
} from '../components/enrichments/EnrichmentConfigFields';
import { EditableLeadsGrid } from '../components/enrichments/EditableLeadsGrid';
import { EnrichedResultsGrid } from '../components/enrichments/EnrichedResultsGrid';
import { useEnrichment } from '../hooks/useEnrichments';
import { queryKeys } from '../hooks/queryKeys';

export function TestEnrichment() {
  const { projectId, enrichmentId } = useParams();
  const projId = Number(projectId);
  const enrId = Number(enrichmentId);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { notify, notifyError } = useNotify();
  const { requireKeys } = useApiKeysDialog();
  const { data: enrichment, isLoading } = useEnrichment(enrId);

  const [config, setConfig] = useState<EnrichmentConfig | null>(null);
  const [leads, setLeads] = useState<string[]>([]);
  const [leadsSeeded, setLeadsSeeded] = useState(false);
  const [result, setResult] = useState<EnrichLeadsResponse | null>(null);

  // Seed the editable config from the enrichment once loaded.
  useEffect(() => {
    if (enrichment && !config) setConfig(configFromEnrichment(enrichment));
  }, [enrichment, config]);

  // Seed up to 5 test leads from the merged results (once).
  useQuery({
    queryKey: [...queryKeys.mergedResults(projId), 'test-leads'],
    queryFn: async () => {
      const merged = await getMergedResults(projId);
      const first = (merged.data ?? [])
        .slice(0, 5)
        .map((row) => String(row.lead ?? ''))
        .filter(Boolean);
      if (!leadsSeeded) {
        setLeads(first);
        setLeadsSeeded(true);
      }
      return first;
    },
    enabled: !Number.isNaN(projId) && !leadsSeeded,
  });

  const saveMutation = useMutation({
    mutationFn: () => {
      const c = config!;
      return updateEnrichment(enrId, {
        column_name: c.column_name.trim(),
        goal: c.goal,
        acceptable_evidence: c.acceptable_evidence,
        result_format: c.result_format,
        // Clear non-applicable format fields so stale values don't leak through.
        result_true_if: c.result_format === 'True/False' ? c.result_true_if : '',
        result_false_if: c.result_format === 'True/False' ? c.result_false_if : '',
        result_number_value: c.result_format === 'Number' ? c.result_number_value : '',
        result_text_value: c.result_format === 'Text' ? c.result_text_value : '',
      });
    },
    onSuccess: (updated) => {
      notify('Enrichment configuration saved.', 'success');
      setConfig(configFromEnrichment(updated));
      queryClient.invalidateQueries({ queryKey: queryKeys.enrichment(enrId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.enrichments(projId) });
    },
    onError: notifyError,
  });

  const runMutation = useMutation({
    mutationFn: () => {
      const leadsData: LeadRow[] = leads
        .map((lead) => lead.trim())
        .filter(Boolean)
        .map((lead) => ({ lead }));
      if (leadsData.length === 0) {
        throw new Error('No test leads to enrich. Add at least one lead.');
      }
      return testEnrichLeads(projId, enrId, leadsData);
    },
    onSuccess: (data) => {
      setResult(data);
      notify(`Test enrichment completed on ${data.leads_processed} lead(s).`, 'success');
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

  const resultColumns = useMemo(() => {
    if (!config?.column_name) return undefined;
    const col = config.column_name;
    return ['lead', col, `${col}_reasoning`, `${col}_evidence`];
  }, [config]);

  if (isLoading || !config)
    return <Typography color="text.secondary">Loading enrichment...</Typography>;
  if (!enrichment) return <Typography color="error">No enrichment selected.</Typography>;

  const patch = (p: Partial<EnrichmentConfig>) => setConfig((c) => (c ? { ...c, ...p } : c));

  return (
    <Box>
      <PageHeader
        title={`Test Enrichment — ${enrichment.enrichment_name}`}
        actions={
          <Button
            variant="outlined"
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate(`/projects/${projId}/enrichments/${enrId}/review`)}
          >
            Back to Review
          </Button>
        }
      />

      <Card variant="outlined" sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Test Leads (first 5)
          </Typography>
          <EditableLeadsGrid leads={leads} onChange={setLeads} />
        </CardContent>
      </Card>

      <Card variant="outlined" sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Edit Enrichment Configuration
          </Typography>
          <EnrichmentConfigFields config={config} onChange={patch} />
          <Box sx={{ mt: 2 }}>
            <LoadingButton
              variant="contained"
              startIcon={<SaveIcon />}
              loading={saveMutation.isPending}
              onClick={() => saveMutation.mutate()}
            >
              Save Configuration
            </LoadingButton>
          </Box>
        </CardContent>
      </Card>

      <LoadingButton
        variant="contained"
        color="secondary"
        startIcon={<PlayArrowIcon />}
        loading={runMutation.isPending}
        onClick={handleRun}
      >
        Run Enrichment on Test Leads
      </LoadingButton>
      {runMutation.isPending && (
        <Alert severity="warning" sx={{ mt: 2 }}>
          Running enrichment — this can take a few minutes. Please don't navigate away.
        </Alert>
      )}

      {result && (
        <Box sx={{ mt: 3 }}>
          <Typography variant="h6" gutterBottom>
            Test Results
          </Typography>
          <EnrichedResultsGrid
            columns={result.columns}
            rows={result.enriched_leads}
            onlyColumns={resultColumns}
          />
        </Box>
      )}
    </Box>
  );
}
