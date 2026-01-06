export const ALPHA_NUMERIC_TOKENS = [
  'A','B','C','D','E','F','G','H','I','J','K','L','M',
  'N','O','P','Q','R','S','T','U','V','W','X','Y','Z',
  '0','1','2','3','4','5','6','7','8','9',
];

export const getInitialToken = (value: string | null | undefined) => {
  if (!value) return null;
  const trimmed = value.trim();
  if (!trimmed) return null;
  const initial = trimmed.charAt(0).toUpperCase();
  return /^[A-Z0-9]$/.test(initial) ? initial : null;
};
