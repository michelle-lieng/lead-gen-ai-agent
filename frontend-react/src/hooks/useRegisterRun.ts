/**
 * The clerk.
 *
 * Takes each message sent to the project's one chat, lets the agent decide
 * whether it asks for companies, research columns or both, runs that work,
 * and reports what is actually happening while it works.
 *
 * Everything reported here is measured, never simulated. Steps advance at real
 * call boundaries, counts come from real responses, and enrichment is sent in
 * small batches specifically so the progress reported is the progress made.
 * Nothing invents a per-item counter for work the backend runs as one call.
 *
 * Its account is written into the project's saved conversation (see
 * useProjectChat), not kept here, so it outlives the visit.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { interpretMessage } from '../api/chat';
import { draftEnrichment, enrichLeads, getUnansweredColumns } from '../api/enrichments';
import { getMergedResults } from '../api/mergedResults';
import {
  draftLeadBrief,
  generateLeads,
  generateQueries,
  generateUrls,
  searchPlaces,
} from '../api/leadsSerp';
import { ChatEntryCreate, ContinueColumn, LeadRow, MessagePlan, ServerKeys } from '../api/types';
import { errorToMessage } from '../api/errors';
import {
  CANCELLED_LINE,
  STARTED_LINE,
  hasWork,
  needsConfirmation,
  summarisePlan,
} from '../components/panel/breakdown';
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

export type LogTone = 'step' | 'result' | 'error';

export type RunKind = 'find' | 'enrich';

export interface RunState {
  kind: RunKind | null;
  instruction: string;
  running: boolean;
  steps: RunStep[];
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
  startedAt: null,
  workingLeads: new Set(),
  settling: new Set(),
  workingField: null,
};

export function useRegisterRun(
  projectId: number,
  record: (entry: ChatEntryCreate) => void,
) {
  const queryClient = useQueryClient();
  // Read when a run starts, not at render, so a run sees the latest status.
  const hasGoogleKey = () =>
    Boolean(queryClient.getQueryData<ServerKeys>(queryKeys.serverKeys)?.google);
  const [state, setState] = useState<RunState>(EMPTY);
  const abortRef = useRef(false);
  const runningRef = useRef(false);
  const recordRef = useRef(record);
  recordRef.current = record;
  const settleTimer = useRef<number>();

  runningRef.current = state.running;

  const leftRef = useRef(false);

  const write = useCallback((text: string, tone: LogTone = 'step') => {
    // A call still in flight when the project closed may answer afterwards;
    // the thread already says the run stopped, so it stays quiet from here.
    if (leftRef.current) return;
    recordRef.current({ role: 'log', kind: tone, text });
  }, []);

  useEffect(() => {
    // Reset on (re)mount: StrictMode mounts twice in development.
    leftRef.current = false;
    return () => {
      // Runs are driven from this page, so leaving the project ends one. Say
      // so in the thread, or it would read as though the run just went quiet.
      if (runningRef.current) {
        write('Run stopped: left the project.', 'error');
      }
      leftRef.current = true;
      abortRef.current = true;
      window.clearTimeout(settleTimer.current);
    };
  }, [write]);

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

  /**
   * Search for companies and add them to the table. Reports into steps whose
   * ids start with `find-`. Returns false when it failed, so the caller stops.
   */
  const runFind = useCallback(
    async (instruction: string, location: string): Promise<boolean> => {
      let stepId = 'find-brief';
      try {
        setStep('find-brief', { status: 'running' });
        const brief = await draftLeadBrief(projectId, instruction);
        setStep('find-brief', {
          status: 'done',
          detail: `${brief.num_queries} queries planned`,
        });
        write(`Target set: ${brief.query_search_target}`);
        write(`Counts as a lead: ${brief.lead_minimum_criteria}`);
        if (abortRef.current) return true;

        // A named place means Google Maps lists the businesses there, so ask
        // it first. It is an extra source: if it fails, the web search runs.
        if (location) {
          if (hasGoogleKey()) {
            setStep('find-places', { status: 'running' });
            write(`Google Places · ${instruction}`);
            try {
              const places = await searchPlaces(projectId, instruction, location);
              const leftOut = places.not_businesses
                ? ` · ${places.not_businesses} left out as not businesses`
                : '';
              write(
                `${places.found} ${places.found === 1 ? 'business' : 'businesses'} found on Google Maps${leftOut} · ${places.new} new, ${places.existing} already in the table.`,
                'result',
              );
              setStep('find-places', { status: 'done', detail: `${places.found} found` });
              markSettled(places.leads);
              refreshRegister();
            } catch (error) {
              const message = errorToMessage(error);
              write(message, 'error');
              setStep('find-places', { status: 'failed', detail: message });
            }
            if (abortRef.current) return true;
          } else {
            write(
              `Set GOOGLE_PLACES_API_KEY in the backend's environment to also search Google Maps for ${location}.`,
            );
          }
        }

        stepId = 'find-queries';
        setStep('find-queries', { status: 'running' });
        const queries = await generateQueries(projectId, brief.num_queries);
        setStep('find-queries', {
          status: 'done',
          detail: `${queries.length} ${queries.length === 1 ? 'query' : 'queries'}`,
        });
        queries.forEach((query) => write(`Query · ${query}`));
        if (abortRef.current) return true;

        stepId = 'find-urls';
        setStep('find-urls', { status: 'running' });
        const urls = await generateUrls(projectId, queries);
        setStep('find-urls', {
          status: 'done',
          detail: `${urls.urls_added} sources from ${urls.queries_processed} queries`,
        });
        write(`${urls.urls_added} sources located.`, 'result');
        if (urls.urls_added === 0) {
          setStep('find-extract', { status: 'skipped' });
          write('No sources to read. Try a broader request.', 'error');
          return true;
        }
        if (abortRef.current) return true;

        stepId = 'find-extract';
        setStep('find-extract', {
          status: 'running',
          detail: `reading ${urls.urls_added} sources`,
        });
        write(`Reading ${urls.urls_added} sources. This takes a few minutes.`);
        const extraction = await generateLeads(projectId);
        setStep('find-extract', {
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
        return true;
      } catch (error) {
        const message = errorToMessage(error);
        write(message, 'error');
        refreshRegister();
        finish(stepId, message);
        return false;
      }
    },
    [projectId, write, setStep, finish, markSettled, refreshRegister],
  );

  /* ---------------------------------------------------------- add a column */

  /**
   * Fill one research column: either a new one drafted from a question, or an
   * existing one being finished for the leads it has no answer for yet.
   * Reports into the steps `<prefix>-draft` (new columns only) and
   * `<prefix>-research`. Returns false when it failed.
   */
  const runColumn = useCallback(
    async (
      prefix: string,
      source: { question: string; resultFormat?: 'True/False' } | { existing: ContinueColumn },
      leads: string[],
    ): Promise<boolean> => {
      const draftId = `${prefix}-draft`;
      const researchId = `${prefix}-research`;
      const batches = Math.ceil(leads.length / ENRICH_BATCH);
      let stepId = draftId;
      let enrichment: { id: number; enrichment_name: string };
      let answered = 0;

      try {
        if ('question' in source) {
          setStep(draftId, { status: 'running' });
          const drafted = await draftEnrichment(projectId, source.question, source.resultFormat);
          enrichment = drafted;
          setStep(draftId, { status: 'done', detail: drafted.column_name ?? undefined });
          setState((current) => ({ ...current, workingField: drafted.column_name ?? null }));
          write(`Column “${drafted.enrichment_name}” · ${drafted.result_format}`, 'result');
          if (drafted.goal) write(`Looking for: ${drafted.goal}`);
          queryClient.invalidateQueries({ queryKey: queryKeys.enrichments(projectId) });
          // Pull the results too: the new column should appear in the table as
          // soon as it exists, not only once its first answers land.
          queryClient.invalidateQueries({ queryKey: queryKeys.mergedResults(projectId) });
          if (abortRef.current) return true;
        } else {
          const { existing } = source;
          enrichment = { id: existing.enrichment_id, enrichment_name: existing.name };
          setState((current) => ({ ...current, workingField: existing.column_name }));
          write(
            `Continuing column “${existing.name}” for the ${leads.length} ${
              leads.length === 1 ? 'entry' : 'entries'
            } without an answer yet.`,
            'result',
          );
        }

        if (leads.length === 0) {
          // The column exists now; the next search fills it for its new rows.
          setStep(researchId, { status: 'skipped', detail: 'no companies yet' });
          write(
            `No companies to research yet. “${enrichment.enrichment_name}” will be filled for the companies the next search finds.`,
            'result',
          );
          return true;
        }

        stepId = researchId;
        setStep(researchId, {
          label: `Research ${leads.length} ${leads.length === 1 ? 'entry' : 'entries'}`,
          status: 'running',
          detail: `0 of ${leads.length}`,
        });

        for (let start = 0; start < leads.length; start += ENRICH_BATCH) {
          if (abortRef.current) {
            write(`Stopped after ${answered} of ${leads.length}.`, 'result');
            break;
          }

          const batch = leads.slice(start, start + ENRICH_BATCH);
          setState((current) => ({ ...current, workingLeads: new Set(batch) }));

          const payload: LeadRow[] = batch.map((lead) => ({ lead }));
          const result = await enrichLeads(projectId, enrichment.id, payload);

          answered += result.leads_processed;
          setStep(researchId, {
            status: 'running',
            detail: `${answered} of ${leads.length}`,
          });
          write(
            `Batch ${Math.floor(start / ENRICH_BATCH) + 1} of ${batches} · ${result.leads_processed} answered.`,
          );
          markSettled(batch);
          queryClient.invalidateQueries({
            queryKey: queryKeys.mergedResults(projectId),
          });
        }

        setStep(researchId, {
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
        setState((current) => ({ ...current, workingLeads: new Set(), workingField: null }));
        refreshRegister();
        return true;
      } catch (error) {
        const message = errorToMessage(error);
        write(message, 'error');
        if (answered > 0) {
          write(`${answered} entries were answered before this failed.`, 'result');
        }
        refreshRegister();
        finish(stepId, message);
        return false;
      }
    },
    [projectId, write, setStep, finish, markSettled, refreshRegister, queryClient],
  );

  /* ------------------------------------------------------------ one message */

  /**
   * Handle one message sent to the project's chat. The agent decides what it
   * asks for (companies, research columns, both, or just an answer) and the
   * matching work runs in order: companies first, so new columns are
   * researched for the new rows as well.
   */
  /**
   * Run a confirmed plan: companies first, then new rows filled for existing
   * columns, then criteria, research columns and any columns being continued.
   * Its steps are appended to whatever the panel already shows.
   */
  const execute = useCallback(
    async (plan: MessagePlan) => {
      const planned: RunStep[] = [];
      if (plan.find) {
        planned.push(
          { id: 'find-brief', label: `Search: ${plan.find_instruction}`, status: 'pending' },
          ...(plan.location && hasGoogleKey()
            ? [{ id: 'find-places', label: 'Search Google Maps', status: 'pending' as const }]
            : []),
          { id: 'find-queries', label: 'Write search queries', status: 'pending' },
          { id: 'find-urls', label: 'Locate sources', status: 'pending' },
          { id: 'find-extract', label: 'Read sources and extract companies', status: 'pending' },
        );
      }
      plan.criteria.forEach((criterion, index) => {
        planned.push(
          { id: `crit-${index}-draft`, label: `Check: ${criterion}`, status: 'pending' },
          { id: `crit-${index}-research`, label: 'Research every entry', status: 'pending' },
        );
      });
      plan.columns.forEach((column, index) => {
        planned.push(
          { id: `col-${index}-draft`, label: `Define column: ${column}`, status: 'pending' },
          { id: `col-${index}-research`, label: 'Research every entry', status: 'pending' },
        );
      });
      plan.continue_columns.forEach((column, index) => {
        planned.push({
          id: `cont-${index}-research`,
          label: `Continue column: ${column.name}`,
          status: 'pending',
        });
      });

      setState((current) => ({ ...current, steps: [...current.steps, ...planned] }));
      const newColumns = plan.criteria.length + plan.columns.length;

      /** The table's leads as they stand now, read fresh. */
      const readLeads = async (): Promise<string[]> => {
        const results = await queryClient.fetchQuery({
          queryKey: queryKeys.mergedResults(projectId),
          queryFn: () => getMergedResults(projectId),
          staleTime: 0,
        });
        return results.data.map((row) => String(row.lead ?? '')).filter(Boolean);
      };

      // Leads each column was just filled for, so continuing that column in
      // the same message never researches them twice.
      const filled = new Map<number, Set<string>>();

      if (plan.find) {
        setState((current) => ({ ...current, kind: 'find' }));
        let before: Set<string>;
        try {
          before = new Set(await readLeads());
        } catch (error) {
          const text = errorToMessage(error);
          write(text, 'error');
          return finish('find-brief', text);
        }
        write(`Base search: ${plan.find_instruction}`);
        if (!(await runFind(plan.find_instruction, plan.location))) return;
        if (abortRef.current) return finish();

        // Existing columns are filled for the rows this search added, so a
        // criterion never reads blank for new companies. Only the new rows:
        // gaps the user left on purpose (a stopped column) are not refilled.
        let gaps: ContinueColumn[];
        try {
          gaps = (await getUnansweredColumns(projectId))
            .map((gap) => ({ ...gap, leads: gap.leads.filter((lead) => !before.has(lead)) }))
            .filter((gap) => gap.leads.length > 0);
        } catch (error) {
          const text = errorToMessage(error);
          write(text, 'error');
          return finish('find-extract', text);
        }
        if (gaps.length > 0) {
          const afterFind = (step: RunStep) => step.id === 'find-extract';
          setState((current) => {
            const at = current.steps.findIndex(afterFind) + 1;
            const added: RunStep[] = gaps.map((gap, index) => ({
              id: `gap-${index}-research`,
              label: `Fill new rows: ${gap.name}`,
              status: 'pending',
            }));
            return {
              ...current,
              steps: [...current.steps.slice(0, at), ...added, ...current.steps.slice(at)],
            };
          });
          setState((current) => ({ ...current, kind: 'enrich' }));
          for (const [index, gap] of gaps.entries()) {
            if (abortRef.current) return finish();
            if (!(await runColumn(`gap-${index}`, { existing: gap }, gap.leads))) return;
            filled.set(gap.enrichment_id, new Set(gap.leads));
          }
        }
      }

      if (newColumns > 0) {
        setState((current) => ({ ...current, kind: 'enrich' }));
        const firstStep = plan.criteria.length > 0 ? 'crit-0-draft' : 'col-0-draft';
        let leads: string[];
        try {
          // Read the table fresh: a search that just ran has added rows.
          leads = await readLeads();
        } catch (error) {
          const text = errorToMessage(error);
          write(text, 'error');
          return finish(firstStep, text);
        }
        // After a search that found nothing, the columns are still created so
        // the request isn't lost; without a search there is nothing to add to.
        if (leads.length === 0 && !plan.find) {
          write(
            'There are no companies in the table to research yet. Ask me to find some first.',
            'error',
          );
          return finish(firstStep, 'no companies yet');
        }
        for (const [index, criterion] of plan.criteria.entries()) {
          if (abortRef.current) return finish();
          write(`Criterion column: ${criterion} · Yes/No`);
          const source = { question: criterion, resultFormat: 'True/False' as const };
          if (!(await runColumn(`crit-${index}`, source, leads))) return;
        }
        for (const [index, column] of plan.columns.entries()) {
          if (abortRef.current) return finish();
          if (!(await runColumn(`col-${index}`, { question: column }, leads))) return;
        }
      }

      // Finishing a column only touches the leads it has no answer for, as
      // they stood when the message was read.
      for (const [index, column] of plan.continue_columns.entries()) {
        if (abortRef.current) break;
        const done = filled.get(column.enrichment_id);
        const leads = done ? column.leads.filter((lead) => !done.has(lead)) : column.leads;
        if (leads.length === 0) {
          setStep(`cont-${index}-research`, {
            status: 'skipped',
            detail: 'already filled above',
          });
          continue;
        }
        setState((current) => ({ ...current, kind: 'enrich' }));
        if (!(await runColumn(`cont-${index}`, { existing: column }, leads))) return;
      }

      finish();
    },
    [projectId, write, setStep, finish, runFind, runColumn, queryClient],
  );

  const ask = useCallback(
    async (message: string) => {
      abortRef.current = false;
      setState({
        ...EMPTY,
        instruction: message,
        running: true,
        startedAt: Date.now(),
        steps: [{ id: 'understand', label: 'Read the request', status: 'pending' }],
      });
      recordRef.current({ role: 'user', kind: 'text', text: message });

      let plan: MessagePlan;
      try {
        setStep('understand', { status: 'running' });
        const raw = await interpretMessage(projectId, message);
        // An older backend may leave fields out; a missing list must not
        // throw mid-run and leave the chat stuck on "running".
        plan = {
          find: Boolean(raw.find),
          find_instruction: raw.find_instruction ?? '',
          location: raw.location ?? '',
          criteria: raw.criteria ?? [],
          columns: raw.columns ?? [],
          continue_columns: raw.continue_columns ?? [],
          reply: raw.reply ?? '',
        };
      } catch (error) {
        const text = errorToMessage(error);
        write(text, 'error');
        finish('understand', text);
        return;
      }

      const count = (n: number, one: string, many: string) =>
        n === 1 ? one : n > 1 ? many.replace('#', String(n)) : null;
      const summary = [
        plan.find ? 'find companies' : null,
        count(plan.criteria.length, 'check 1 criterion', 'check # criteria'),
        count(plan.columns.length, 'add 1 column', 'add # columns'),
        count(plan.continue_columns.length, 'continue 1 column', 'continue # columns'),
      ].filter(Boolean);
      setState((current) => ({
        ...current,
        steps: [
          ...current.steps.map((step) =>
            step.id === 'understand'
              ? {
                  ...step,
                  status: 'done' as const,
                  detail: summary.length ? summary.join(' and ') : 'answered',
                }
              : step,
          ),
        ],
      }));

      if (plan.reply) recordRef.current({ role: 'agent', kind: 'text', text: plan.reply });
      if (!hasWork(plan)) {
        if (!plan.reply) {
          write(
            'Nothing to do for that message. Describe the companies you want, or a question to answer about each one.',
            'result',
          );
        }
        return finish();
      }

      // A search or new columns wait for the user to confirm them on a card.
      if (needsConfirmation(plan)) {
        recordRef.current({
          role: 'agent',
          kind: 'breakdown',
          text: summarisePlan(plan),
          payload: { plan },
        });
        // Nothing has run: clear the run state, so the panel shows the card
        // alone rather than a "Finished" run beside it.
        setState(EMPTY);
        return;
      }

      await execute(plan);
    },
    [projectId, write, setStep, finish, execute],
  );

  /** Start a plan the user confirmed (and perhaps edited) on its card. */
  const start = useCallback(
    async (plan: MessagePlan) => {
      abortRef.current = false;
      setState({ ...EMPTY, instruction: summarisePlan(plan), running: true, startedAt: Date.now() });
      write(STARTED_LINE, 'result');
      await execute(plan);
    },
    [write, execute],
  );

  /** Drop the plan on the newest card. */
  const cancel = useCallback(() => {
    write(CANCELLED_LINE, 'result');
    setState(EMPTY);
  }, [write]);

  return { ...state, ask, start, cancel, stop, clear };
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
