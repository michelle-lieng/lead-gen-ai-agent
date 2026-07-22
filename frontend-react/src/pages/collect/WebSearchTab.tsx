import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Divider,
  Grid,
  IconButton,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import TravelExploreIcon from '@mui/icons-material/TravelExplore';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import DownloadIcon from '@mui/icons-material/Download';
import SaveIcon from '@mui/icons-material/Save';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import {
  fetchLatestRunZip,
  generateLeads,
  generateQueries,
  generateUrls,
  getQueries,
} from '../../api/leadsSerp';
import { updateProject } from '../../api/projects';
import { LeadExtractionResponse, Project } from '../../api/types';
import { useApiKeysDialog } from '../../components/apiKeys/ApiKeysProvider';
import { LoadingButton } from '../../components/common/LoadingButton';
import { StatCard } from '../../components/common/StatCard';
import { useNotify } from '../../components/common/Notifications';
import { queryKeys } from '../../hooks/queryKeys';
import { triggerDownload, formatDateTime } from '../../utils/download';
import { UrlsEditor } from './UrlsEditor';

const exists = (list: string[], value: string) =>
  list.some((q) => q.toLowerCase() === value.toLowerCase());

export function WebSearchTab({ project }: { project: Project }) {
  const projectId = project.id;
  const queryClient = useQueryClient();
  const { notify, notifyError } = useNotify();
  const { requireKeys } = useApiKeysDialog();

  const [queries, setQueries] = useState<string[]>([]);
  const [customQuery, setCustomQuery] = useState('');
  const [searchTarget, setSearchTarget] = useState(project.query_search_target ?? '');
  const [numQueries, setNumQueries] = useState(3);
  const [criteria, setCriteria] = useState(project.lead_minimum_criteria ?? '');
  const [extraction, setExtraction] = useState<LeadExtractionResponse | null>(null);

  useEffect(() => {
    setSearchTarget(project.query_search_target ?? '');
    setCriteria(project.lead_minimum_criteria ?? '');
  }, [project.query_search_target, project.lead_minimum_criteria]);

  const pastQueries = useQuery({
    queryKey: queryKeys.queries(projectId),
    queryFn: () => getQueries(projectId),
  });

  const invalidateProject = () =>
    queryClient.invalidateQueries({ queryKey: queryKeys.project(projectId) });

  // ---- Step 1: queries ----
  const addCustomQuery = () => {
    const value = customQuery.trim();
    if (!value) return;
    if (exists(queries, value)) {
      notify('That query is already in your list.', 'warning');
      return;
    }
    setQueries((prev) => [...prev, value]);
    setCustomQuery('');
  };

  const generateQueriesMutation = useMutation({
    mutationFn: async () => {
      if (searchTarget.trim() && searchTarget !== project.query_search_target) {
        await updateProject(projectId, { query_search_target: searchTarget.trim() });
        invalidateProject();
      }
      return generateQueries(projectId, numQueries);
    },
    onSuccess: (generated) => {
      let added = 0;
      let skipped = 0;
      setQueries((prev) => {
        const next = [...prev];
        for (const q of generated) {
          if (exists(next, q)) skipped += 1;
          else {
            next.push(q);
            added += 1;
          }
        }
        return next;
      });
      notify(`Added ${added} queries${skipped ? `, skipped ${skipped} duplicate(s)` : ''}.`, 'success');
    },
    onError: notifyError,
  });

  const handleGenerateQueries = () => {
    if (!searchTarget.trim()) {
      notify('Enter a query search target first.', 'warning');
      return;
    }
    if (!requireKeys()) return;
    generateQueriesMutation.mutate();
  };

  // ---- Step 2: URLs ----
  const generateUrlsMutation = useMutation({
    mutationFn: () => generateUrls(projectId, queries),
    onSuccess: (result) => {
      notify(
        `Generated ${result.urls_added} URLs from ${result.queries_processed} queries.`,
        'success',
      );
      queryClient.invalidateQueries({ queryKey: queryKeys.urls(projectId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.queries(projectId) });
    },
    onError: notifyError,
  });

  const handleGenerateUrls = () => {
    if (queries.length === 0) {
      notify('Add at least one query first.', 'warning');
      return;
    }
    if (!requireKeys()) return;
    generateUrlsMutation.mutate();
  };

  // ---- Step 3: extract ----
  const saveCriteriaMutation = useMutation({
    mutationFn: () => updateProject(projectId, { lead_minimum_criteria: criteria.trim() }),
    onSuccess: () => {
      notify('Lead criteria saved.', 'success');
      invalidateProject();
    },
    onError: notifyError,
  });

  const extractMutation = useMutation({
    mutationFn: () => generateLeads(projectId),
    onSuccess: async (result) => {
      setExtraction(result);
      notify(`Extracted ${result.new_leads_extracted} new lead(s).`, 'success');
      invalidateProject();
      queryClient.invalidateQueries({ queryKey: queryKeys.urls(projectId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.mergedResults(projectId) });
    },
    onError: notifyError,
  });

  const handleExtract = () => {
    if (!criteria.trim()) {
      notify('Save your lead criteria first.', 'warning');
      return;
    }
    if (!requireKeys()) return;
    setExtraction(null);
    extractMutation.mutate();
  };

  const downloadMutation = useMutation({
    mutationFn: () => fetchLatestRunZip(projectId),
    onSuccess: (file) => {
      if (!file) {
        notify('No results to download yet.', 'info');
        return;
      }
      triggerDownload(file);
      notify(`Download ready: ${file.filename}`, 'success');
    },
    onError: notifyError,
  });

  const anyRunning =
    generateUrlsMutation.isPending || extractMutation.isPending;

  return (
    <Box>
      {/* Step 1 */}
      <Typography variant="h6" gutterBottom>
        Step 1 · Search Queries
      </Typography>

      <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
        <TextField
          label="Add custom query"
          value={customQuery}
          onChange={(e) => setCustomQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && addCustomQuery()}
          fullWidth
          size="small"
        />
        <Button variant="outlined" startIcon={<AddIcon />} onClick={addCustomQuery}>
          Add
        </Button>
      </Stack>

      <Accordion variant="outlined" sx={{ mb: 2 }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <AutoAwesomeIcon fontSize="small" /> Generate AI queries (optional)
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={2} alignItems="flex-start">
            <Grid item xs={12} md={9}>
              <TextField
                label="Query search target"
                value={searchTarget}
                onChange={(e) => setSearchTarget(e.target.value)}
                fullWidth
                multiline
                minRows={2}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField
                label="Number of queries"
                type="number"
                value={numQueries}
                onChange={(e) =>
                  setNumQueries(Math.max(1, Math.min(20, Number(e.target.value) || 1)))
                }
                inputProps={{ min: 1, max: 20 }}
                fullWidth
              />
            </Grid>
          </Grid>
          <LoadingButton
            variant="contained"
            startIcon={<AutoAwesomeIcon />}
            sx={{ mt: 2 }}
            loading={generateQueriesMutation.isPending}
            onClick={handleGenerateQueries}
          >
            Generate Smart Queries
          </LoadingButton>
        </AccordionDetails>
      </Accordion>

      {queries.length > 0 && (
        <Card variant="outlined" sx={{ mb: 2 }}>
          <CardContent>
            <Typography variant="subtitle1" gutterBottom>
              Your search queries ({queries.length})
            </Typography>
            <Stack spacing={1}>
              {queries.map((query, index) => (
                <Stack key={index} direction="row" spacing={1} alignItems="center">
                  <TextField
                    value={query}
                    onChange={(e) =>
                      setQueries((prev) =>
                        prev.map((q, i) => (i === index ? e.target.value : q)),
                      )
                    }
                    size="small"
                    fullWidth
                  />
                  <IconButton
                    aria-label="remove"
                    onClick={() =>
                      setQueries((prev) => prev.filter((_, i) => i !== index))
                    }
                  >
                    <DeleteIcon />
                  </IconButton>
                </Stack>
              ))}
            </Stack>
          </CardContent>
        </Card>
      )}

      {pastQueries.data && pastQueries.data.length > 0 && (
        <Accordion variant="outlined" sx={{ mb: 2 }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography>Previously run queries ({pastQueries.data.length})</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <TableContainer sx={{ maxHeight: 260 }}>
              <Table size="small" stickyHeader>
                <TableHead>
                  <TableRow>
                    <TableCell>Query</TableCell>
                    <TableCell>Date Added</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {pastQueries.data.map((q) => (
                    <TableRow key={q.id}>
                      <TableCell>{q.query}</TableCell>
                      <TableCell>{formatDateTime(q.date_added)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </AccordionDetails>
        </Accordion>
      )}

      <Divider sx={{ my: 3 }} />

      {/* Step 2 */}
      <Typography variant="h6" gutterBottom>
        Step 2 · Validate URLs
      </Typography>
      {anyRunning && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          A long-running operation is in progress — please don't navigate away.
        </Alert>
      )}
      <LoadingButton
        variant="contained"
        startIcon={<TravelExploreIcon />}
        loading={generateUrlsMutation.isPending}
        disabled={queries.length === 0}
        onClick={handleGenerateUrls}
        sx={{ mb: 2 }}
      >
        Generate URLs
      </LoadingButton>
      <UrlsEditor projectId={projectId} />

      <Divider sx={{ my: 3 }} />

      {/* Step 3 */}
      <Typography variant="h6" gutterBottom>
        Step 3 · Extract Leads
      </Typography>
      <Stack direction="row" spacing={1} sx={{ mb: 2 }} alignItems="flex-start">
        <TextField
          label="Bare minimum lead criteria"
          value={criteria}
          onChange={(e) => setCriteria(e.target.value)}
          fullWidth
          multiline
          minRows={2}
        />
        <LoadingButton
          variant="outlined"
          startIcon={<SaveIcon />}
          loading={saveCriteriaMutation.isPending}
          disabled={!criteria.trim()}
          onClick={() => saveCriteriaMutation.mutate()}
          sx={{ mt: 1 }}
        >
          Save Criteria
        </LoadingButton>
      </Stack>
      <LoadingButton
        variant="contained"
        startIcon={<SmartToyIcon />}
        loading={extractMutation.isPending}
        disabled={!criteria.trim()}
        onClick={handleExtract}
      >
        {extraction ? 'Re-run Extraction' : 'Extract Leads'}
      </LoadingButton>
      {extractMutation.isPending && (
        <Alert severity="warning" sx={{ mt: 2 }}>
          Extracting leads — this can take several minutes. Please don't navigate away.
        </Alert>
      )}

      {extraction && (
        <Box sx={{ mt: 3 }}>
          <Typography variant="subtitle1" gutterBottom>
            Extraction Results
          </Typography>
          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={6} md={2.4}>
              <StatCard label="Leads Extracted" value={extraction.new_leads_extracted} />
            </Grid>
            <Grid item xs={6} md={2.4}>
              <StatCard label="URLs Processed" value={extraction.urls_processed} />
            </Grid>
            <Grid item xs={6} md={2.4}>
              <StatCard label="URLs Skipped" value={extraction.urls_skipped} />
            </Grid>
            <Grid item xs={6} md={2.4}>
              <StatCard label="URLs Failed" value={extraction.urls_failed} />
            </Grid>
            <Grid item xs={6} md={2.4}>
              <StatCard label="Total URLs" value={extraction.total_urls_attempted} />
            </Grid>
          </Grid>
          <TableContainer sx={{ maxHeight: 360, border: '1px solid #e0e0e0' }}>
            <Table size="small" stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell>Status</TableCell>
                  <TableCell>Query</TableCell>
                  <TableCell>URL</TableCell>
                  <TableCell>Leads Found</TableCell>
                  <TableCell>Leads</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {extraction.extracted_leads.map((row, i) => (
                  <TableRow key={i}>
                    <TableCell>{row.status}</TableCell>
                    <TableCell>{row.query}</TableCell>
                    <TableCell sx={{ maxWidth: 240, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {row.url}
                    </TableCell>
                    <TableCell>{row.leads.length}</TableCell>
                    <TableCell>
                      {row.leads.slice(0, 5).join(', ')}
                      {row.leads.length > 5 ? '…' : ''}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      )}

      <Divider sx={{ my: 3 }} />

      {/* Download */}
      <Typography variant="h6" gutterBottom>
        Download Webscraped Leads
      </Typography>
      {project.leads_collected > 0 ? (
        <LoadingButton
          variant="outlined"
          startIcon={<DownloadIcon />}
          loading={downloadMutation.isPending}
          onClick={() => downloadMutation.mutate()}
        >
          Download All Results (ZIP)
        </LoadingButton>
      ) : (
        <Typography color="text.secondary">
          No leads collected yet. Run an extraction first.
        </Typography>
      )}
    </Box>
  );
}
