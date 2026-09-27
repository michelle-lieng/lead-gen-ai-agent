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
import { Enrichment, QueryRecord } from '../../api/types';
import { ThreadLine } from '../../hooks/useProjectChat';
import { RunStep, formatElapsed } from '../../hooks/useRegisterRun';
import { Icon } from '../ui/Icon';
import { Button, IconButton, Spinner } from '../ui/Primitives';

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

            <Thread lines={thread} />

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
  enrichments,
  pastQueries,
  onUseExample,
}: {
  copy: typeof COPY;
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
            {copy.examples.map((example) => (
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
function Thread({ lines }: { lines: ThreadLine[] }) {
  if (lines.length === 0) return null;
  return (
    <div className="log thread">
      {lines.map((line, index) => {
        const previous = lines[index - 1];
        const newDay = !previous || dayKey(previous.at) !== dayKey(line.at);
        return (
          <Fragment key={line.key}>
            {newDay && <p className="thread__day">{dayLabel(line.at)}</p>}
            {line.role === 'user' ? (
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
