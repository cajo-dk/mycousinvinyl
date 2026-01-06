/**
 * Loading spinner component.
 */

import './Loading.css';

interface LoadingProps {
  message?: string;
}

export function Loading({ message = 'Loading...' }: LoadingProps) {
  return (
    <div className="loading">
      <div className="loading-spinner"></div>
      <p className="loading-message">{message}</p>
    </div>
  );
}
