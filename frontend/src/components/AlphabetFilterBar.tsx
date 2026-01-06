import { ALPHA_NUMERIC_TOKENS } from '@/utils/alpha';
import './AlphabetFilterBar.css';

interface AlphabetFilterBarProps {
  active: string | null;
  available: Set<string>;
  onSelect: (value: string | null) => void;
  className?: string;
}

export function AlphabetFilterBar({ active, available, onSelect, className }: AlphabetFilterBarProps) {
  return (
    <div className={`alphabet-filter ${className ?? ''}`.trim()}>
      {ALPHA_NUMERIC_TOKENS.map((token) => {
        const isEnabled = available.has(token);
        const isActive = active === token;
        return (
          <button
            key={token}
            type="button"
            className={`alphabet-filter-button ${isEnabled ? 'is-enabled' : 'is-disabled'} ${isActive ? 'is-active' : ''}`}
            onClick={() => onSelect(isActive ? null : token)}
            disabled={!isEnabled}
            aria-pressed={isActive}
          >
            {token}
          </button>
        );
      })}
    </div>
  );
}
