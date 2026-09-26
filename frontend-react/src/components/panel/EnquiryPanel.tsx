/**
 * The enquiry panel — the one thing a grid database does not have.
 *
 * Two tabs, the run's own account of what it did, and a composer at the foot.
 * Everything reported here is measured: real step boundaries, real counts, real
 * elapsed time. There is no percentage bar, because nothing in the pipeline
 * knows a percentage.
 */

import { KeyboardEvent, useEffect, useRef, useState } from 'react';
import { Enrichment, QueryRecord } from '../../api/types';
import { LogLine, RunKind, RunStep, formatElapsed } from '../../hooks/useRegisterRun';
import { Icon } from '../ui/Icon';
import { Button, IconButton, Segmented, Spinner } from '../ui/Primitives';

export type PanelTab = 'find' | 'enrich';

const TABS: { id: PanelTab; label: string }[] = [
  { id: 'find', label: 'Find leads' },
  { id: 'enrich', label: 'Enrich leads' },
];

const COPY: Record<PanelTab, { placeholder: string; examples: string[]; note: string }> = {
  find: {
    placeholder: 'Describe the companies you want. One sentence is enough.',
    examples: [
      'Dental clinics in Sydney',
      'Australian manufacturers publishing sustainability reports',
      'Allied health practices in regional Victoria',
    ],
    note: 'Writes the search queries, reads every source it finds, and adds each company to the table as a record.',
  },
  enrich: {
    placeholder: 'Ask one question about every company in the table.',
    examples: [
      'Does this clinic have more than one doctor?',
      'How many locations do they operate?',
      'What is their main contact email address?',
    ],
    note: 'Adds a field, researches every record, and writes the answers in — with the reasoning and evidence behind each one.',
  },
};

interface EnquiryPanelProps {
  tab: PanelTab;
  onTabChange: (tab: PanelTab) => void;
  kind: RunKind | null;
  running: boolean;
  steps: RunStep[];
  log: LogLine[];
  startedAt: number | null;
  instruction: string;
  recordCount: number;
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
  tab,
  onTabChange,
  kind,
  running,
  steps,
  log,
  startedAt,
  instruction,
  recordCount,
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

  // The run account is a transcript: follow the newest line.
  useEffect(() => {
    bodyRef.current?.scrollTo({ top: bodyRef.current.scrollHeight, behavior: 'smooth' });
  }, [log.length, steps]);

  // The `+` at the end of the header row lands here.
  useEffect(() => {
    if (focusToken > 0) inputRef.current?.focus();
  }, [focusToken]);

  const copy = COPY[tab];
  const blockedReason =
    tab === 'enrich' && recordCount === 0
      ? 'Find some companies first — there is nothing to research yet.'
      : null;

  const submit = () => {
    const value = draft.trim();
    if (!value || running || blockedReason) return;
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

  return (
    <aside className="panel" aria-label="Find and enrich leads">
      <div className="panel__head">
        <h2>Ask the agent</h2>
        <IconButton icon="close" label="Hide this panel" compact onClick={onClose} />
      </div>

      <div className="panel__tabs">
        <Segmented
          items={TABS}
          value={tab}
          onChange={onTabChange}
          label="What to ask for"
          busyValue={running ? kind : null}
        />
      </div>

      {running && <div className="panel__progress" role="presentation" />}

      <div
        className="panel__body"
        id="panel-body"
        role="tabpanel"
        aria-labelledby={`tab-${tab}`}
        ref={bodyRef}
      >
        {!showsRun ? (
          <PanelIntro
            copy={copy}
            tab={tab}
            enrichments={enrichments}
            pastQueries={pastQueries}
            onUseExample={(text) => {
              setDraft(text);
              inputRef.current?.focus();
            }}
          />
        ) : (
          <>
            <div className="run__request">
              <span>{kind === 'find' ? 'Asked for' : 'Field requested'}</span>
              <p>{instruction}</p>
            </div>

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

            {log.length > 0 && (
              <div className="log">
                {log.map((line) => (
                  <p key={line.id} className="log__line" data-tone={line.tone}>
                    <time>{stamp(line.at)}</time>
                    <span>{line.text}</span>
                  </p>
                ))}
              </div>
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

        {blockedReason && !running && <p className="composer__blocked">{blockedReason}</p>}

        <textarea
          ref={inputRef}
          className="input composer__input"
          rows={3}
          value={draft}
          placeholder={copy.placeholder}
          disabled={running || Boolean(blockedReason)}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={onKeyDown}
          aria-label={
            tab === 'find'
              ? 'Describe the companies to find'
              : 'Ask one question about every record'
          }
        />

        <div className="composer__foot">
          <span className="composer__hint">
            {running
              ? 'Leave this page open while it works.'
              : tab === 'enrich' && recordCount > 0
                ? `Will research ${recordCount} ${recordCount === 1 ? 'record' : 'records'}.`
                : 'Enter to send · Shift + Enter for a new line'}
          </span>
          <Button
            tone="primary"
            icon={tab === 'find' ? 'search' : 'plus'}
            loading={running}
            disabled={!draft.trim() || Boolean(blockedReason)}
            onClick={submit}
          >
            {tab === 'find' ? 'Find leads' : 'Add field'}
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
  tab,
  enrichments,
  pastQueries,
  onUseExample,
}: {
  copy: (typeof COPY)[PanelTab];
  tab: PanelTab;
  enrichments: Enrichment[];
  pastQueries: QueryRecord[];
  onUseExample: (text: string) => void;
}) {
  // Once a project has a history, that history is more useful than three examples.
  const showHistory = tab === 'find' && pastQueries.length > 0;
  const showFields = tab === 'enrich' && enrichments.length > 0;

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
