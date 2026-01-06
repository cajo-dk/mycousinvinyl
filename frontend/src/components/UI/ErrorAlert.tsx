/**
 * Error alert component.
 */

import './ErrorAlert.css';

interface ErrorAlertProps {
  message: string;
  onRetry?: () => void;
}

export function ErrorAlert({ message, onRetry }: ErrorAlertProps) {
  return (
    <div className="error-alert">
      <div className="error-icon">⚠️</div>
      <div className="error-content">
        <h3>Error</h3>
        <p>{message}</p>
        {onRetry && (
          <button onClick={onRetry} className="error-retry-button">
            Try Again
          </button>
        )}
      </div>
    </div>
  );
}
