import { useEffect, useRef, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { mdiMenu } from '@mdi/js';
import { Icon } from './Icon';
import './ResponsiveRowActions.css';

export interface ResponsiveRowAction {
  key: string;
  label: string;
  iconPath?: string;
  onClick: () => void;
  displayLabel?: string;
  buttonClassName?: string;
  disabled?: boolean;
  title?: string;
}

interface ResponsiveRowActionsProps {
  primaryActions: ResponsiveRowAction[];
  overflowActions: ResponsiveRowAction[];
  menuAriaLabel?: string;
}

export function ResponsiveRowActions({
  primaryActions,
  overflowActions,
  menuAriaLabel = 'More actions',
}: ResponsiveRowActionsProps) {
  const [isOverflowOpen, setIsOverflowOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const location = useLocation();

  useEffect(() => {
    setIsOverflowOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    const handleOutsideClick = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOverflowOpen(false);
      }
    };
    document.addEventListener('mousedown', handleOutsideClick);
    return () => document.removeEventListener('mousedown', handleOutsideClick);
  }, []);

  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsOverflowOpen(false);
      }
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, []);

  return (
    <div className="responsive-row-actions" ref={containerRef}>
      {primaryActions.map((action) => (
        <button
          key={action.key}
          type="button"
          className={`btn-action ${action.buttonClassName || ''}`.trim()}
          onClick={action.onClick}
          title={action.title || action.label}
          aria-label={action.label}
          disabled={action.disabled}
        >
          {action.iconPath && <Icon path={action.iconPath} />}
          {action.displayLabel && <span>{action.displayLabel}</span>}
        </button>
      ))}
      {overflowActions.length > 0 && (
        <div className={`responsive-row-actions-overflow ${isOverflowOpen ? 'menu-open' : ''}`.trim()}>
          <button
            type="button"
            className="btn-action responsive-row-actions-menu-toggle"
            onClick={() => setIsOverflowOpen((prev) => !prev)}
            aria-label={menuAriaLabel}
            aria-haspopup="menu"
            aria-expanded={isOverflowOpen}
            title={menuAriaLabel}
          >
            <Icon path={mdiMenu} />
          </button>
          <div
            className={`responsive-row-actions-menu ${isOverflowOpen ? 'open' : ''}`}
            role="menu"
          >
            {overflowActions.map((action) => (
              <button
                key={action.key}
                type="button"
                className={action.buttonClassName}
                onClick={() => {
                  action.onClick();
                  setIsOverflowOpen(false);
                }}
                role="menuitem"
                disabled={action.disabled}
              >
                {action.iconPath && <Icon path={action.iconPath} />}
                <span>{action.label}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
