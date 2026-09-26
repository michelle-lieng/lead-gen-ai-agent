/**
 * The clerk.
 *
 * Runs the two jobs the register supports — finding leads and enriching them —
 * from one plain-English instruction, and reports what is actually happening
 * while it works.
 *
 * Everything reported here is measured, never simulated. Steps advance at real
 * call boundaries, counts come from real responses, and enrichment is sent in
 * small batches specifically so the progress reported is the progress made.
 * Nothing invents a per-item counter for work the backend runs as one call.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { draftEnrichment, enrichLeads } from '../api/enrichments';
import {
  draftLeadBrief,
  generateLeads,
  generateQueries,
  generateUrls,
} from '../api/leadsSerp';
import { Enrichment, LeadRow } from '../api/types';
import { errorToMessage } from '../api/errors';
import { queryKeys } from './queryKeys';

export type StepStatus =
  | 'pending'
  | 'running'
  | 'done'
  | 'failed'
  | 'skipped'
  /** The user stopped the run on purpose — not a failure. */
  | 'stopped';

export interface RunStep {
  id: string;
  label: string;
  status: StepStatus;
  /** The measured outcome, written once the step closes. */
  detail?: string;
}

export interface LogLine {
  id: number;
  at: Date;
  text: string;
  tone: 'step' | 'result' | 'error';
}

export type RunKind = 'find' | 'enrich';

export interface RunState {
  kind: RunKind | null;
  instruction: string;
  running: boolean;
  steps: RunStep[];
  log: LogLine[];
  startedAt: number | null;
  /** Entries currently being worked, marked by the setting rule. */
  workingLeads: Set<string>;
  /** Entries whose answers just landed, so their cells ink in. */
  settling: Set<string>;
  /**
   * The column being filled right now. Only cells in this field may show a
   * pending mark: without it, a blank cell in some unrelated column reads as
   * though the agent were researching that instead.
   */
  workingField: string | null;
}

/** Leads sent per enrichment call. Small enough that progress is frequent,
 *  large enough that the backend's internal concurrency still pays off. */
const ENRICH_BATCH = 10;

const EMPTY: RunState = {
  kind: null,
  instruction: '',
  running: false,
  steps: [],
  log: [],
  startedAt: null,
  workingLeads: new Set(),
  settling: new Set(),
  workingField: null,
};

export function useRegisterRun(projectId: number) {
  const queryClient = useQueryClient();
  const [state, setState] = useState<RunState>(EMPTY);
  const abortRef = useRef(false);
  const logId = useRef(1);
  const settleTimer = useRef<number>();

  useEffect(
    () => () => {
      abortRef.current = true;
      window.clearTimeout(settleTimer.current);
    },
    [],
  );

  const write = useCallback((text: string, tone: LogLine['tone'] = 'step') => {
    setState((current) => ({
      ...current,
      log: [...current.log, { id: logId.current++, at: new Date(), text, tone }],
    }));
  }, []);

  const setStep = useCallback((id: string, patch: Partial<RunStep>) => {
    setState((current) => ({
      ...current,
      steps: current.steps.map((step) =>
        step.id === id ? { ...step, ...patch } : step,
      ),
    }));
  }, []);

  /** Ink in a batch of entries, then let them settle back to normal ink. */
  const markSettled = useCallback((leads: string[]) => {
    setState((current) => ({ ...current, settling: new Set(leads) }));
    window.clearTimeout(settleTimer.current);
    settleTimer.current = window.setTimeout(() => {
      setState((current) => ({ ...current, settling: new Set() }));
    }, 1400);
  }, []);

  const refreshRegister = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: queryKeys.mergedResults(projectId) });
    queryClient.invalidateQueries({ queryKey: queryKeys.project(projectId) });
    queryClient.invalidateQueries({ queryKey: queryKeys.enrichments(projectId) });
  }, [projectId, queryClient]);

  const finish = useCallback((failedStepId?: string, message?: string) => {
    setState((current) => ({
      ...current,
      running: false,
      workingLeads: new Set(),
      workingField: null,
      steps: current.steps.map((step) => {
        if (step.id === failedStepId) return { ...step, status: 'failed', detail: message };
        if (step.status === 'pending' || step.status === 'running') {
          return { ...step, status: failedStepId ? 'skipped' : step.status };
        }
        return step;
      }),
    }));
  }, []);

  const clear = useCallback(() => {
    setState(EMPTY);
  }, []);

  const stop = useCallback(() => {
    abortRef.current = true;
    write('Stopping after the batch in hand finishes.', 'result');
  }, [write]);

  /* ------------------------------------------------------------- find leads */

  const findLeads = useCallback(
    async (instruction: string) => {
      abortRef.current = false;
      setState({
        ...EMPTY,
        kind: 'find',
        instruction,
        running: true,
        startedAt: Date.now(),
        steps: [
          { id: 'brief', label: 'Read the request', status: 'pending' },
          { id: 'queries', label: 'Write search queries', status: 'pending' },
          { id: 'urls', label: 'Locate sources', status: 'pending' },
          { id: 'extract', label: 'Read sources and extract companies', status: 'pending' },
        ],
      });
      write(`Request: ${instruction}`, 'result');

      let stepId = 'brief';
      try {
        setStep('brief', { status: 'running' });
        const brief = await draftLeadBrief(projectId, instruction);
        setStep('brief', {
          status: 'done',
          detail: `${brief.num_queries} queries planned`,
        });
        write(`Target set: ${brief.query_search_target}`);
        write(`Counts as a lead: ${brief.lead_minimum_criteria}`);
        if (abortRef.current) return finish();

        stepId = 'queries';
        setStep('queries', { status: 'running' });
        const queries = await generateQueries(projectId, brief.num_queries);
        setStep('queries', {
          status: 'done',
          detail: `${queries.length} ${queries.length === 1 ? 'query' : 'queries'}`,
        });
        queries.forEach((query) => write(`Query · ${query}`));
        if (abortRef.current) return finish();

        stepId = 'urls';
        setStep('urls', { status: 'running' });
        const urls = await generateUrls(projectId, queries);
        setStep('urls', {
          status: 'done',
          detail: `${urls.urls_added} sources from ${urls.queries_processed} queries`,
        });
        write(`${urls.urls_added} sources located.`, 'result');
        if (urls.urls_added === 0) {
          write('No sources to read. Try a broader request.', 'error');
          return finish();
        }
        if (abortRef.current) return finish();

        stepId = 'extract';
        setStep('extract', {
          status: 'running',
          detail: `reading ${urls.urls_added} sources`,
        });
        write(`Reading ${urls.urls_added} sources. This takes a few minutes.`);
        const extraction = await generateLeads(projectId);
        setStep('extract', {
          status: 'done',
          detail: `${extraction.new_leads_extracted} new ${
            extraction.new_leads_extracted === 1 ? 'entry' : 'entries'
          }`,
        });

        write(
          `${extraction.urls_processed} read · ${extraction.urls_skipped} skipped · ${extraction.urls_failed} failed.`,
          'result',
        );
        write(
          `${extraction.new_leads_extracted} new ${
            extraction.new_leads_extracted === 1 ? 'entry' : 'entries'
          } added to the register.`,
          'result',
        );

        const found = extraction.extracted_leads.flatMap((row) => row.leads);
        markSettled(found);
        refreshRegister();
        finish();
      } catch (error) {
        const message = errorToMessage(error);
        write(message, 'error');
        refreshRegister();
        finish(stepId, message);
      }
    },
    [projectId, write, setStep, finish, markSettled, refreshRegister],
  );

  /* ----------------------------------------------------------- enrich leads */

  const enrichRegister = useCallback(
    async (instruction: string, leads: string[]) => {
      abortRef.current = false;
      const batches = Math.ceil(leads.length / ENRICH_BATCH);

      setState({
        ...EMPTY,
        kind: 'enrich',
        instruction,
        running: true,
        startedAt: Date.now(),
        steps: [
          { id: 'draft', label: 'Define the column', status: 'pending' },
          {
            id: 'research',
            label: `Research ${leads.length} ${leads.length === 1 ? 'entry' : 'entries'}`,
            status: 'pending',
          },
        ],
      });
      write(`Request: ${instruction}`, 'result');

      let stepId = 'draft';
      let enrichment: Enrichment | null = null;
      let answered = 0;

      try {
        setStep('draft', { status: 'running' });
        enrichment = await draftEnrichment(projectId, instruction);
        setStep('draft', { status: 'done', detail: enrichment.column_name ?? undefined });
        setState((current) => ({ ...current, workingField: enrichment?.column_name ?? null }));
        write(`Column “${enrichment.enrichment_name}” · ${enrichment.result_format}`, 'result');
        if (enrichment.goal) write(`Looking for: ${enrichment.goal}`);
        queryClient.invalidateQueries({ queryKey: queryKeys.enrichments(projectId) });
        // Pull the results too: the new column should appear in the table as
        // soon as it exists, not only once its first answers land.
        queryClient.invalidateQueries({ queryKey: queryKeys.mergedResults(projectId) });
        if (abortRef.current) return finish();

        stepId = 'research';
        setStep('research', { status: 'running', detail: `0 of ${leads.length}` });

        for (let index = 0; index < leads.length; index += ENRICH_BATCH) {
          if (abortRef.current) {
            write(`Stopped after ${answered} of ${leads.length}.`, 'result');
            break;
          }

          const batch = leads.slice(index, index + ENRICH_BATCH);
          setState((current) => ({ ...current, workingLeads: new Set(batch) }));

          const payload: LeadRow[] = batch.map((lead) => ({ lead }));
          const result = await enrichLeads(projectId, enrichment.id, payload);

          answered += result.leads_processed;
          setStep('research', {
            status: 'running',
            detail: `${answered} of ${leads.length}`,
          });
          write(
            `Batch ${Math.floor(index / ENRICH_BATCH) + 1} of ${batches} · ${result.leads_processed} answered.`,
          );
          markSettled(batch);
          queryClient.invalidateQueries({
            queryKey: queryKeys.mergedResults(projectId),
          });
        }

        setStep('research', {
          status: abortRef.current ? 'stopped' : 'done',
          detail: abortRef.current
            ? `stopped after ${answered} of ${leads.length}`
            : `${answered} of ${leads.length} answered`,
        });
        write(
          abortRef.current
            ? `Stopped. Column “${enrichment.enrichment_name}” holds ${answered} ${
                answered === 1 ? 'answer' : 'answers'
              }; the rest are still blank.`
            : `Column “${enrichment.enrichment_name}” filled for ${answered} ${
                answered === 1 ? 'entry' : 'entries'
              }.`,
          'result',
        );
        refreshRegister();
        finish();
      } catch (error) {
        const message = errorToMessage(error);
        write(message, 'error');
        if (answered > 0) {
          write(`${answered} entries were answered before this failed.`, 'result');
        }
        refreshRegister();
        finish(stepId, message);
      }
    },
    [projectId, write, setStep, finish, markSettled, refreshRegister, queryClient],
  );

  return { ...state, findLeads, enrichRegister, stop, clear };
}

/** Format a duration as the register prints it: 1m 04s. */
export function formatElapsed(ms: number): string {
  const total = Math.max(0, Math.floor(ms / 1000));
  const minutes = Math.floor(total / 60);
  const seconds = total % 60;
  return minutes > 0
    ? `${minutes}m ${String(seconds).padStart(2, '0')}s`
    : `${seconds}s`;
}
