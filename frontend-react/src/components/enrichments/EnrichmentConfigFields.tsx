import { MenuItem, Stack, TextField } from '@mui/material';
import { Enrichment, ResultFormat } from '../../api/types';

export interface EnrichmentConfig {
  column_name: string;
  goal: string;
  acceptable_evidence: string;
  result_format: ResultFormat;
  result_true_if: string;
  result_false_if: string;
  result_number_value: string;
  result_text_value: string;
}

export const RESULT_FORMATS: ResultFormat[] = ['', 'True/False', 'Text', 'Number'];

/** Build a config object from an enrichment record. */
export function configFromEnrichment(e: Enrichment): EnrichmentConfig {
  return {
    column_name: e.column_name ?? '',
    goal: e.goal ?? '',
    acceptable_evidence: e.acceptable_evidence ?? '',
    result_format: (e.result_format ?? '') as ResultFormat,
    result_true_if: e.result_true_if ?? '',
    result_false_if: e.result_false_if ?? '',
    result_number_value: e.result_number_value ?? '',
    result_text_value: e.result_text_value ?? '',
  };
}

/** Return a list of missing required fields for the given config (empty = valid). */
export function validateConfig(config: EnrichmentConfig): string[] {
  const missing: string[] = [];
  if (!config.column_name.trim()) missing.push('Column Name');
  if (!config.goal.trim()) missing.push('Goal');
  if (!config.acceptable_evidence.trim()) missing.push('Agent Reasoning');
  if (!config.result_format) missing.push('Result Format');
  if (config.result_format === 'True/False') {
    if (!config.result_true_if.trim()) missing.push('True if');
    if (!config.result_false_if.trim()) missing.push('False if');
  } else if (config.result_format === 'Number') {
    if (!config.result_number_value.trim()) missing.push('Number output');
  } else if (config.result_format === 'Text') {
    if (!config.result_text_value.trim()) missing.push('Text output');
  }
  return missing;
}

interface EnrichmentConfigFieldsProps {
  config: EnrichmentConfig;
  disabled?: boolean;
  onChange?: (patch: Partial<EnrichmentConfig>) => void;
}

export function EnrichmentConfigFields({
  config,
  disabled = false,
  onChange,
}: EnrichmentConfigFieldsProps) {
  const set = (patch: Partial<EnrichmentConfig>) => onChange?.(patch);

  return (
    <Stack spacing={2}>
      <TextField
        label="Column Name"
        required
        disabled={disabled}
        value={config.column_name}
        onChange={(e) => set({ column_name: e.target.value })}
        placeholder="e.g. more_than_1_doctor"
        fullWidth
      />
      <TextField
        label="Goal"
        required
        disabled={disabled}
        value={config.goal}
        onChange={(e) => set({ goal: e.target.value })}
        fullWidth
        multiline
        minRows={2}
      />
      <TextField
        label="Agent Reasoning (acceptable evidence)"
        required
        disabled={disabled}
        value={config.acceptable_evidence}
        onChange={(e) => set({ acceptable_evidence: e.target.value })}
        fullWidth
        multiline
        minRows={2}
      />
      <TextField
        select
        label="Result Format"
        required
        disabled={disabled}
        value={config.result_format}
        onChange={(e) => set({ result_format: e.target.value as ResultFormat })}
        fullWidth
      >
        {RESULT_FORMATS.map((format) => (
          <MenuItem key={format || 'none'} value={format}>
            {format || '(choose one)'}
          </MenuItem>
        ))}
      </TextField>

      {config.result_format === 'True/False' && (
        <>
          <TextField
            label="True if"
            required
            disabled={disabled}
            value={config.result_true_if}
            onChange={(e) => set({ result_true_if: e.target.value })}
            fullWidth
          />
          <TextField
            label="False if"
            required
            disabled={disabled}
            value={config.result_false_if}
            onChange={(e) => set({ result_false_if: e.target.value })}
            fullWidth
          />
        </>
      )}
      {config.result_format === 'Number' && (
        <TextField
          label="Define the Number Output"
          required
          disabled={disabled}
          value={config.result_number_value}
          onChange={(e) => set({ result_number_value: e.target.value })}
          fullWidth
        />
      )}
      {config.result_format === 'Text' && (
        <TextField
          label="Define the Text Output"
          required
          disabled={disabled}
          value={config.result_text_value}
          onChange={(e) => set({ result_text_value: e.target.value })}
          fullWidth
        />
      )}
    </Stack>
  );
}
