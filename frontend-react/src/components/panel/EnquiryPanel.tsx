/**
 * The enquiry panel — the one thing a grid database does not have.
 *
 * One chat per project: the saved conversation (every request and the run's
 * own account of what it did) and a single composer at the foot. The agent
 * decides whether a message asks for companies, research columns or both, so
 * there is nothing to switch between.
 * Everything reported here is measured: real step boundaries, real counts, real
 * elapsed time. There is no percentage bar, because nothing in the pipeline
 * knows a percentage.
 */

import { Fragment, KeyboardEvent, useEffect, useRef, useState } from 'react';
import { Enrichment, MessagePlan, QueryRecord } from '../../api/types';
import { ThreadLine } from '../../hooks/useProjectChat';
import { RunStep, formatElapsed } from '../../hooks/useRegisterRun';
import { useApiKeys } from '../../store/apiKeys';
import { Icon } from '../ui/Icon';
import { Button, IconButton, Spinner } from '../ui/Primitives';
import {
  applyCardEdits,
  cardState,
  hasWork,
  isActiveCard,
  readCardPlan,
} from './breakdown';

const COPY = {
  placeholder: 'Describe the companies you want, or ask something about each one.',
  examples: [
    'Dental clinics in Sydney',
    'Australian manufacturers publishing sustainability reports',
    'Does each company have more than 50 staff?',
  ],
  note: 'Describe the companies you want and they are found and added as records. Ask a question about them and it becomes a column, researched for every record with the reasoning and evidence behind each answer. Ask for more at any time: this chat carries on where it left off.',
};

interface EnquiryPanelProps {
  running: boolean;
  steps: RunStep[];
  /** The project's conversation, oldest first. */
  thread: ThreadLine[];
  /** False until the saved conversation has loaded; nothing is sent before. */
  threadReady: boolean;
  threadError: unknown;
  hasEarlier: boolean;
  loadingEarlier: boolean;
  onLoadEarlier: () => void;
  /** Lines written but not yet confirmed saved. */
  unsaved: number;
  startedAt: number | null;
  enrichments: Enrichment[];
  pastQueries: QueryRecord[];
  onSubmit: (instruction: string) => void;
  /** Example first messages written for this project; generic ones when empty. */
  examples?: string[] | null;
  /** Run the plan on the newest card, as the user edited it. */
  onStart: (plan: MessagePlan) => void;
  /** Drop the plan on the newest card. */
  onCancel: () => void;
  onStop: () => void;
  onClear: () => void;
  onClose: () => void;
  /** Bumped when the grid's `+` asks for the composer; focuses it. */
  focusToken: number;
}

export function EnquiryPanel({
  running,
  steps,
  thread,
  threadReady,
  threadError,
  hasEarlier,
  loadingEarlier,
  onLoadEarlier,
  unsaved,
  startedAt,
  enrichments,
  pastQueries,
  onSubmit,
  examples,
  onStart,
  onCancel,
  onStop,
  onClear,
  onClose,
  focusToken,
}: EnquiryPanelProps) {
  const [draft, setDraft] = useState('');
  const bodyRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const elapsed = useElapsed(running ? startedAt : null);

  // The conversation is a transcript: follow the newest line. Loading earlier
  // lines prepends them, so that must not yank the view back to the bottom.
  const newestKey = thread[thread.length - 1]?.key;
  useEffect(() => {
    bodyRef.current?.scrollTo({ top: bodyRef.current.scrollHeight, behavior: 'smooth' });
  }, [newestKey, steps]);

  // The `+` at the end of the header row lands here.
  useEffect(() => {
    if (focusToken > 0) inputRef.current?.focus();
  }, [focusToken]);

  const copy = COPY;

  const submit = () => {
    const value = draft.trim();
    if (!value || running || !threadReady) return;
    onSubmit(value);
    setDraft('');
  };

  const onKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      submit();
    }
  };

  const showsRun = steps.length > 0;
  const showsThread = thread.length > 0;

  return (
    <aside className="panel" aria-label="Agent chat">
      <div className="panel__head">
        <h2>Ask the agent</h2>
        <IconButton icon="close" label="Hide this panel" compact onClick={onClose} />
      </div>

      {running && <div className="panel__progress" role="presentation" />}

      <div
        className="panel__body"
        id="panel-body"
        aria-live="polite"
        ref={bodyRef}
      >
        {threadError ? (
          <p className="composer__blocked">
            This project's conversation couldn't be loaded. Reload the page to try again.
          </p>
        ) : !threadReady ? (
          <p className="intro__note">
            <Spinner size={11} /> Loading this project's conversation…
          </p>
        ) : !showsThread && !showsRun ? (
          <PanelIntro
            copy={copy}
            enrichments={enrichments}
            pastQueries={pastQueries}
            examples={examples?.length ? examples : copy.examples}
            onUseExample={(text) => {
              setDraft(text);
              inputRef.current?.focus();
            }}
          />
        ) : (
          <>
            {hasEarlier && (
              <div className="thread__earlier">
                <Button tone="quiet" compact loading={loadingEarlier} onClick={onLoadEarlier}>
                  Load earlier messages
                </Button>
              </div>
            )}

            <Thread lines={thread} running={running} onStart={onStart} onCancel={onCancel} />

            {showsRun && (
            <ol className="steps">
              {steps.map((step) => (
                <li key={step.id} data-status={step.status}>
                  <span className="steps__mark" aria-hidden="true">
                    {step.status === 'running' ? (
                      <Spinner size={11} />
                    ) : step.status === 'done' ? (
                      <Icon name="check" size={13} />
                    ) : step.status === 'failed' ? (
                      <Icon name="alert" size={13} />
                    ) : (
                      <span className="steps__dash" />
                    )}
                  </span>
                  <span>
                    {step.label}
                    {step.detail && <span className="steps__detail"> — {step.detail}</span>}
                    <span className="sr-only">. {STATUS_WORD[step.status]}</span>
                  </span>
                </li>
              ))}
            </ol>
            )}
          </>
        )}
      </div>

      <div className="composer">
        {showsRun && (
          <div className="composer__status">
            {running ? (
              <>
                <Spinner size={11} />
                <b>Working</b>
                <span>· {formatElapsed(elapsed)}</span>
                <Button tone="quiet" compact icon="stop" onClick={onStop}>
                  Stop
                </Button>
              </>
            ) : (
              <>
                <b>Finished</b>
                <Button tone="quiet" compact onClick={onClear}>
                  Start another
                </Button>
              </>
            )}
          </div>
        )}

        {unsaved > 0 && !running && (
          <p className="composer__hint">
            {unsaved} {unsaved === 1 ? 'line' : 'lines'} not saved yet. Retrying.
          </p>
        )}

        <textarea
          ref={inputRef}
          className="input composer__input"
          rows={3}
          value={draft}
          placeholder={copy.placeholder}
          disabled={running || !threadReady}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={onKeyDown}
          aria-label="Message the agent"
        />

        <div className="composer__foot">
          <span className="composer__hint">
            {running
              ? 'Leave this page open while it works.'
              : 'Enter to send · Shift + Enter for a new line'}
          </span>
          <Button
            tone="primary"
            icon="sparkle"
            loading={running}
            disabled={!draft.trim() || !threadReady}
            onClick={submit}
          >
            Send
          </Button>
        </div>
      </div>
    </aside>
  );
}

/* ---------------------------------------------------------------- internals */

const STATUS_WORD: Record<RunStep['status'], string> = {
  pending: 'Not started',
  running: 'Running',
  done: 'Done',
  failed: 'Failed',
  skipped: 'Skipped',
  stopped: 'Stopped',
};

function PanelIntro({
  copy,
  examples,
  enrichments,
  pastQueries,
  onUseExample,
}: {
  copy: typeof COPY;
  examples: string[];
  enrichments: Enrichment[];
  pastQueries: QueryRecord[];
  onUseExample: (text: string) => void;
}) {
  // Once a project has a history, that history is more useful than three examples.
  const showHistory = pastQueries.length > 0;
  const showFields = enrichments.length > 0;

  return (
    <div>
      <p className="intro__note">{copy.note}</p>

      {!showHistory && !showFields && (
        <>
          <span className="intro__label">Try one of these</span>
          <ul className="intro__examples">
            {examples.map((example) => (
              <li key={example}>
                <button type="button" onClick={() => onUseExample(example)}>
                  {example}
                </button>
              </li>
            ))}
          </ul>
        </>
      )}

      {showHistory && (
        <>
          <span className="intro__label">Searches already run · {pastQueries.length}</span>
          <ul className="intro__queries">
            {pastQueries.slice(0, 12).map((record) => (
              <li key={record.id}>{record.query}</li>
            ))}
          </ul>
          {pastQueries.length > 12 && (
            <p className="intro__more">and {pastQueries.length - 12} more.</p>
          )}
        </>
      )}

      {showFields && (
        <>
          <span className="intro__label">Fields in this table</span>
          <ul className="intro__fields">
            {enrichments.map((enrichment) => (
              <li key={enrichment.id}>
                <span className="head__icon" data-ai="true">
                  <Icon name="sparkle" size={12} />
                </span>
                <b>{enrichment.enrichment_name}</b>
                {enrichment.column_name && <code>{enrichment.column_name}</code>}
              </li>
            ))}
          </ul>
          <p className="intro__more">Ask another question to add a field beside them.</p>
        </>
      )}
    </div>
  );
}

/**
 * The conversation in its log form: a timestamp on every line, the user's own
 * requests set apart, and a divider wherever the day changes so a thread that
 * spans visits reads as one continuing record.
 */
function Thread({
  lines,
  running,
  onStart,
  onCancel,
}: {
  lines: ThreadLine[];
  running: boolean;
  onStart: (plan: MessagePlan) => void;
  onCancel: () => void;
}) {
  if (lines.length === 0) return null;
  return (
    <div className="log thread">
      {lines.map((line, index) => {
        const previous = lines[index - 1];
        const newDay = !previous || dayKey(previous.at) !== dayKey(line.at);
        return (
          <Fragment key={line.key}>
            {newDay && <p className="thread__day">{dayLabel(line.at)}</p>}
            {line.kind === 'breakdown' && readCardPlan(line.payload) ? (
              <BreakdownCard
                at={line.at}
                plan={readCardPlan(line.payload) as MessagePlan}
                active={isActiveCard(lines, index, running)}
                state={cardState(lines, index)}
                onStart={onStart}
                onCancel={onCancel}
              />
            ) : line.role === 'user' ? (
              <div className="thread__request">
                <time>{stamp(line.at)}</time>
                <p>{line.text}</p>
              </div>
            ) : (
              <p className="log__line" data-tone={toneOf(line)} data-role={line.role}>
                <time>{stamp(line.at)}</time>
                <span>{line.text}</span>
              </p>
            )}
          </Fragment>
        );
      })}
    </div>
  );
}

const CARD_STATE_LABEL = {
  started: 'Started',
  cancelled: 'Cancelled',
  replaced: 'Replaced by a newer request',
} as const;

/**
 * What the agent is about to do, before it does it. The base search can be
 * edited and any criterion or column removed; to add one, the user types it
 * in the chat and a new card replaces this one.
 */
function BreakdownCard({
  at,
  plan,
  active,
  state,
  onStart,
  onCancel,
}: {
  at: Date;
  plan: MessagePlan;
  active: boolean;
  state: ReturnType<typeof cardState>;
  onStart: (plan: MessagePlan) => void;
  onCancel: () => void;
}) {
  const [base, setBase] = useState(plan.find_instruction);
  const [removedCriteria, setRemovedCriteria] = useState<number[]>([]);
  const [removedColumns, setRemovedColumns] = useState<number[]>([]);
  const [removedContinue, setRemovedContinue] = useState<number[]>([]);
  const [removedLocation, setRemovedLocation] = useState(false);
  const { googleKey } = useApiKeys();
  const edited = applyCardEdits(plan, {
    base,
    removedCriteria,
    removedColumns,
    removedContinue,
    removedLocation,
  });
  const runnable = hasWork(edited);

  return (
    <div className="plancard" data-active={active || undefined}>
      <div className="plancard__head">
        <time>{stamp(at)}</time>
        <b>{active ? 'Ready to run' : 'Plan'}</b>
        {!active && state !== 'active' && <span className="plancard__state">{CARD_STATE_LABEL[state]}</span>}
      </div>

      {plan.find && (
        <label className="plancard__field">
          <span>Search for</span>
          <input
            className="input"
            value={base}
            disabled={!active}
            onChange={(event) => setBase(event.target.value)}
            aria-label="Base search"
          />
        </label>
      )}

      {plan.find && edited.find && plan.location && !removedLocation && (
        <p className="plancard__chips">
          <span className="chip" data-kind="location" data-off={!googleKey || undefined}>
            <Icon name="search" size={11} /> Google Maps: {plan.location}
            {!googleKey && ' · needs a Google key'}
            {active && (
              <button
                type="button"
                aria-label={`Skip the Google Maps search for ${plan.location}`}
                onClick={() => setRemovedLocation(true)}
              >
                <Icon name="close" size={10} />
              </button>
            )}
          </span>
        </p>
      )}

      {plan.criteria.length > 0 && (
        <div className="plancard__group">
          <span>Yes/No checks</span>
          <p className="plancard__chips">
            {plan.criteria.map((criterion, index) =>
              removedCriteria.includes(index) ? null : (
                <span key={index} className="chip" data-kind="criterion">
                  {criterion}
                  {active && (
                    <button
                      type="button"
                      aria-label={`Remove ${criterion}`}
                      onClick={() => setRemovedCriteria((current) => [...current, index])}
                    >
                      <Icon name="close" size={10} />
                    </button>
                  )}
                </span>
              ),
            )}
          </p>
        </div>
      )}

      {plan.columns.length > 0 && (
        <div className="plancard__group">
          <span>Columns to research</span>
          <p className="plancard__chips">
            {plan.columns.map((column, index) =>
              removedColumns.includes(index) ? null : (
                <span key={index} className="chip" data-kind="column">
                  {column}
                  {active && (
                    <button
                      type="button"
                      aria-label={`Remove ${column}`}
                      onClick={() => setRemovedColumns((current) => [...current, index])}
                    >
                      <Icon name="close" size={10} />
                    </button>
                  )}
                </span>
              ),
            )}
          </p>
        </div>
      )}

      {plan.continue_columns.length > 0 && (
        <div className="plancard__group">
          <span>Columns to finish</span>
          <p className="plancard__chips">
            {plan.continue_columns.map((column, index) =>
              removedContinue.includes(index) ? null : (
                <span key={column.enrichment_id} className="chip" data-kind="continue">
                  {column.name} · {column.leads.length} left
                  {active && (
                    <button
                      type="button"
                      aria-label={`Don't finish ${column.name}`}
                      onClick={() => setRemovedContinue((current) => [...current, index])}
                    >
                      <Icon name="close" size={10} />
                    </button>
                  )}
                </span>
              ),
            )}
          </p>
        </div>
      )}

      {active && (
        <div className="plancard__foot">
          <span className="plancard__hint">
            {runnable ? 'Type in the chat to add something.' : 'Nothing left to run'}
          </span>
          <Button tone="quiet" compact onClick={onCancel}>
            Cancel
          </Button>
          <Button tone="primary" compact icon="sparkle" disabled={!runnable} onClick={() => onStart(edited)}>
            Start
          </Button>
        </div>
      )}
    </div>
  );
}

function toneOf(line: ThreadLine): 'step' | 'result' | 'error' {
  return line.kind === 'result' || line.kind === 'error' ? line.kind : 'step';
}

function dayKey(date: Date): string {
  return `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}`;
}

function dayLabel(date: Date): string {
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1);
  const label = date.toLocaleDateString(undefined, {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    ...(date.getFullYear() !== today.getFullYear() ? { year: 'numeric' } : {}),
  });
  if (dayKey(date) === dayKey(today)) return `Today · ${label}`;
  if (dayKey(date) === dayKey(yesterday)) return `Yesterday · ${label}`;
  return label;
}

function stamp(date: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
}

/** Tick once a second while a run is open, so the elapsed time is truthful. */
function useElapsed(startedAt: number | null): number {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (startedAt === null) return undefined;
    setNow(Date.now());
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [startedAt]);
  return startedAt === null ? 0 : now - startedAt;
}
