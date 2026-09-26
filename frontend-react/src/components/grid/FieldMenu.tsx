/**
 * A field's own menu.
 *
 * It answers the two questions a column raises: what is this, and where did it
 * come from. For an AI field that means the question the agent was actually
 * given and the evidence it was told to accept — the configuration the user
 * never had to write, available when they want to check it.
 *
 * Deleting a field is deliberately absent: removing the enrichment record would
 * leave its column and its data behind in the results table, so the control
 * would look like it had done nothing. That needs a backend change first.
 */

import { FIELD_TYPE_LABEL, GridField } from './fields';
import { PopItem, PopLabel, PopNote, PopRule, Popover } from '../ui/Popover';
import { useNotify } from '../ui/Toasts';

export function FieldMenu({
  field,
  anchor,
  onClose,
  onRename,
}: {
  field: GridField;
  anchor: HTMLElement;
  onClose: () => void;
  onRename: (field: GridField) => void;
}) {
  const { notify } = useNotify();

  const copyIdentifier = async () => {
    if (!field.identifier) return;
    try {
      await navigator.clipboard.writeText(field.identifier);
      notify(`Copied “${field.identifier}”.`, 'success');
    } catch {
      notify('Your browser blocked the clipboard. Select the name to copy it.', 'warning');
    }
    onClose();
  };

  const goal = field.enrichment?.goal?.trim();
  const evidence = field.enrichment?.acceptable_evidence?.trim();

  return (
    <Popover anchor={anchor} label={`${field.name} field`} onClose={onClose} width={286}>
      <PopLabel>
        {FIELD_TYPE_LABEL[field.type]}
        {field.ai ? ' · written by the agent' : ''}
      </PopLabel>

      {field.identifier && <span className="pop__mono">{field.identifier}</span>}

      {field.ai && (
        <PopItem icon="pencil" onClick={() => onRename(field)}>
          Rename field
        </PopItem>
      )}

      {field.identifier && (
        <PopItem icon="copy" onClick={copyIdentifier}>
          Copy field name
        </PopItem>
      )}

      {goal && (
        <>
          <PopRule />
          <PopLabel>What this field asks</PopLabel>
          <PopNote>{goal}</PopNote>
        </>
      )}

      {evidence && (
        <>
          <PopLabel>Evidence it accepts</PopLabel>
          <PopNote>{evidence}</PopNote>
        </>
      )}

      {!field.ai && !goal && (
        <PopNote>
          {field.key === 'lead'
            ? 'The company name every record is matched on. Editing it renames the record.'
            : field.key === 'serp_count'
              ? 'How many search results this company was found in. Collected, not editable.'
              : 'Imported from a spreadsheet.'}
        </PopNote>
      )}
    </Popover>
  );
}
