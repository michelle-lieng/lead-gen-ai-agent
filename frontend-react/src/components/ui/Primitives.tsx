/**
 * The control vocabulary.
 *
 * Every button, field, chip and empty state on every surface is cut from this
 * file, so the same action never looks like two different things in two places.
 * Tones live in the stylesheet rather than here, which means a bare
 * `<label className="btn" data-tone="plain">` (a file picker) is identical to a
 * rendered <Button>.
 */

import {
  ButtonHTMLAttributes,
  InputHTMLAttributes,
  ReactNode,
  TextareaHTMLAttributes,
  forwardRef,
} from 'react';
import { Icon, IconName } from './Icon';

/* ------------------------------------------------------------------ Button */

type ButtonTone = 'primary' | 'plain' | 'quiet' | 'danger' | 'danger-solid';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  tone?: ButtonTone;
  icon?: IconName;
  loading?: boolean;
  compact?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { tone = 'plain', icon, loading = false, compact = false, children, disabled, ...rest },
  ref,
) {
  return (
    <button
      ref={ref}
      type="button"
      className="btn"
      data-tone={tone}
      data-compact={compact || undefined}
      data-icon-only={children ? undefined : 'true'}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...rest}
    >
      {loading ? (
        <Spinner size={compact ? 12 : 13} />
      ) : icon ? (
        <Icon name={icon} size={compact ? 13 : 14} />
      ) : null}
      {children ? <span>{children}</span> : null}
    </button>
  );
});

/** An icon-only control, which still needs a name for anyone not looking at it. */
export const IconButton = forwardRef<
  HTMLButtonElement,
  ButtonHTMLAttributes<HTMLButtonElement> & {
    icon: IconName;
    label: string;
    tone?: ButtonTone;
    compact?: boolean;
    size?: number;
  }
>(function IconButton(
  { icon, label, tone = 'quiet', compact = false, size, ...rest },
  ref,
) {
  return (
    <button
      ref={ref}
      type="button"
      className="btn"
      data-tone={tone}
      data-compact={compact || undefined}
      data-icon-only="true"
      aria-label={label}
      title={label}
      {...rest}
    >
      <Icon name={icon} size={size ?? (compact ? 13 : 14)} />
    </button>
  );
});

export function Spinner({ size = 13 }: { size?: number }) {
  return (
    <span
      className="spinner"
      style={{ width: size, height: size, borderWidth: size <= 11 ? 1.5 : 2 }}
      aria-hidden="true"
    />
  );
}

/* ------------------------------------------------------------------- Field */

interface FieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  hint?: string;
}

export const Field = forwardRef<HTMLInputElement, FieldProps>(function Field(
  { label, hint, id, ...rest },
  ref,
) {
  const inputId = id ?? `f-${label?.replace(/\W+/g, '-').toLowerCase()}`;
  return (
    <div>
      {label && (
        <label className="field-label" htmlFor={inputId}>
          {label}
        </label>
      )}
      <input ref={ref} id={inputId} className="input" {...rest} />
      {hint && <span className="field-hint">{hint}</span>}
    </div>
  );
});

interface AreaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  hint?: string;
}

export const TextArea = forwardRef<HTMLTextAreaElement, AreaProps>(function TextArea(
  { label, hint, id, ...rest },
  ref,
) {
  const inputId = id ?? `t-${label?.replace(/\W+/g, '-').toLowerCase()}`;
  return (
    <div>
      {label && (
        <label className="field-label" htmlFor={inputId}>
          {label}
        </label>
      )}
      <textarea ref={ref} id={inputId} className="input" {...rest} />
      {hint && <span className="field-hint">{hint}</span>}
    </div>
  );
});

/* -------------------------------------------------------- Segmented control */

export function Segmented<T extends string>({
  items,
  value,
  onChange,
  label,
  busyValue,
}: {
  items: { id: T; label: string }[];
  value: T;
  onChange: (id: T) => void;
  label: string;
  /** The item whose work is running, which carries the spinner. */
  busyValue?: T | null;
}) {
  return (
    <div className="segmented" role="tablist" aria-label={label} style={{ flex: 1 }}>
      {items.map((item) => (
        <button
          key={item.id}
          type="button"
          role="tab"
          id={`tab-${item.id}`}
          aria-selected={value === item.id}
          aria-controls="panel-body"
          className="segmented__item"
          style={{ flex: 1, justifyContent: 'center' }}
          onClick={() => onChange(item.id)}
        >
          {busyValue === item.id && <Spinner size={11} />}
          {item.label}
        </button>
      ))}
    </div>
  );
}

/* ------------------------------------------------------------------- Empty */

/**
 * An empty region that teaches the interface: what this holds, the one action
 * that fills it, and — where the sequence matters — what happens next.
 */
export function EmptyState({
  icon = 'sparkle',
  title,
  body,
  actions,
  sequence,
  fill = false,
}: {
  icon?: IconName;
  title: string;
  body: string;
  actions?: ReactNode;
  sequence?: { head: string; body: string }[];
  fill?: boolean;
}) {
  return (
    <div className="empty" data-fill={fill || undefined}>
      <div className="empty__body">
        <span className="empty__glyph" aria-hidden="true">
          <Icon name={icon} size={20} />
        </span>
        <h2 className="empty__title">{title}</h2>
        <p className="empty__note">{body}</p>
        {actions && <div className="empty__action">{actions}</div>}

        {sequence && sequence.length > 0 && (
          <ol className="empty__steps">
            {sequence.map((step, index) => (
              <li key={step.head}>
                <span className="empty__no" aria-hidden="true">
                  {index + 1}
                </span>
                <span>
                  <b>{step.head}</b>
                  <span>{step.body}</span>
                </span>
              </li>
            ))}
          </ol>
        )}
      </div>
    </div>
  );
}
