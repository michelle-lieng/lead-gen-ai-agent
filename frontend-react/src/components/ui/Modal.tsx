/**
 * A dialog: a rounded card over a dimmed ground, used only where the task needs
 * protected focus — entering API keys, mapping an uploaded file's columns,
 * confirming a deletion, and reading one record in full.
 */

import { ReactNode, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { Button, IconButton } from './Primitives';

const FOCUSABLE =
  'a[href], button:not(:disabled), input:not(:disabled), select:not(:disabled), textarea:not(:disabled), [tabindex]:not([tabindex="-1"])';

interface ModalProps {
  open: boolean;
  title?: string;
  note?: string;
  onClose: () => void;
  children: ReactNode;
  footer?: ReactNode;
  width?: number;
  /** Replaces the default title row entirely — used by the expanded record. */
  head?: ReactNode;
  label?: string;
}

export function Modal({
  open,
  title,
  note,
  onClose,
  children,
  footer,
  width = 520,
  head,
  label,
}: ModalProps) {
  const cardRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return undefined;

    const previous = document.activeElement as HTMLElement | null;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.stopPropagation();
        onClose();
        return;
      }
      if (event.key !== 'Tab' || !cardRef.current) return;

      const focusable = cardRef.current.querySelectorAll<HTMLElement>(FOCUSABLE);
      if (focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };

    document.addEventListener('keydown', onKeyDown, true);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    const timer = window.setTimeout(() => {
      cardRef.current
        ?.querySelector<HTMLElement>(
          'input:not(:disabled), textarea:not(:disabled), button:not(:disabled)',
        )
        ?.focus();
    }, 0);

    return () => {
      document.removeEventListener('keydown', onKeyDown, true);
      document.body.style.overflow = previousOverflow;
      window.clearTimeout(timer);
      previous?.focus?.();
    };
  }, [open, onClose]);

  if (!open) return null;

  return createPortal(
    <div
      className="scrim"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div
        ref={cardRef}
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-label={label ?? title}
        style={{ maxWidth: width }}
      >
        {head ?? (
          <div className="modal__head">
            <div style={{ flex: '1 1 auto', minWidth: 0 }}>
              <h2>{title}</h2>
              {note && <p>{note}</p>}
            </div>
            <IconButton icon="close" label="Close" compact onClick={onClose} />
          </div>
        )}

        <div className="modal__body">{children}</div>

        {footer && <div className="modal__foot">{footer}</div>}
      </div>
    </div>,
    document.body,
  );
}

/* ----------------------------------------------------------------- Confirm */

export function Confirm({
  open,
  title,
  message,
  confirmLabel = 'Confirm',
  destructive = false,
  loading = false,
  onConfirm,
  onCancel,
}: {
  open: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  destructive?: boolean;
  loading?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  return (
    <Modal
      open={open}
      title={title}
      onClose={onCancel}
      width={440}
      footer={
        <>
          <Button onClick={onCancel} disabled={loading}>
            Cancel
          </Button>
          <Button
            tone={destructive ? 'danger-solid' : 'primary'}
            loading={loading}
            onClick={onConfirm}
            icon={destructive ? 'trash' : 'check'}
          >
            {confirmLabel}
          </Button>
        </>
      }
    >
      <p style={{ fontSize: 13, lineHeight: 1.6 }}>{message}</p>
    </Modal>
  );
}
