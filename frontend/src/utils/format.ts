const getNumberSeparators = () => {
  const parts = new Intl.NumberFormat().formatToParts(12345.6);
  const group = parts.find((part) => part.type === 'group')?.value ?? ',';
  const decimal = parts.find((part) => part.type === 'decimal')?.value ?? '.';
  return { group, decimal };
};

const escapeRegex = (value: string) => value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

export const formatNumber = (value: number, options?: Intl.NumberFormatOptions) =>
  new Intl.NumberFormat(undefined, options).format(value);

export const formatDecimal = (value: number, fractionDigits = 2) =>
  formatNumber(value, { minimumFractionDigits: fractionDigits, maximumFractionDigits: fractionDigits });

export const formatDate = (value?: string) => {
  if (!value) return '-';
  const trimmed = value.trim();
  if (!trimmed) return '-';
  if (/^\d{4}$/.test(trimmed)) return trimmed;
  const date = new Date(trimmed);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString(undefined);
};

export const formatDateTime = (value?: string) => {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString(undefined);
};

export const parseLocaleNumber = (value: string) => {
  if (value === null || value === undefined) return null;
  let normalized = value.trim();
  if (!normalized) return null;

  const { group, decimal } = getNumberSeparators();
  const hasComma = normalized.includes(',');
  const hasDot = normalized.includes('.');

  normalized = normalized.replace(/[\s\u00A0\u202F]/g, '');

  if (group && group !== decimal) {
    const groupIsDot = group === '.';
    const groupIsComma = group === ',';
    const groupUsedAsDecimal =
      (groupIsDot && decimal === ',' && hasDot && !hasComma) ||
      (groupIsComma && decimal === '.' && hasComma && !hasDot);
    if (!groupUsedAsDecimal) {
      normalized = normalized.replace(new RegExp(escapeRegex(group), 'g'), '');
    }
  }

  if (decimal !== '.') {
    if (normalized.includes(decimal)) {
      normalized = normalized.replace(new RegExp(escapeRegex(decimal), 'g'), '.');
    } else if (decimal === '.' && hasComma && !hasDot) {
      normalized = normalized.replace(',', '.');
    }
  } else if (hasComma && !hasDot) {
    normalized = normalized.replace(',', '.');
  }

  const parsed = Number(normalized);
  return Number.isNaN(parsed) ? null : parsed;
};
