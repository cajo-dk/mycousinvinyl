import { useEffect, useId, useMemo, useState } from 'react';
import './Pager.css';

interface PagerProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  disabled?: boolean;
  className?: string;
  neighborCount?: number;
  infoText?: string;
}

export function Pager({
  currentPage,
  totalPages,
  onPageChange,
  disabled = false,
  className = '',
  neighborCount = 3,
  infoText,
}: PagerProps) {
  const inputId = useId();
  const [inputValue, setInputValue] = useState(String(currentPage));

  useEffect(() => {
    setInputValue(String(currentPage));
  }, [currentPage]);

  const previousPages = useMemo(() => {
    const start = Math.max(1, currentPage - neighborCount);
    return Array.from({ length: currentPage - start }, (_, index) => start + index);
  }, [currentPage, neighborCount]);

  const nextPages = useMemo(() => {
    const end = Math.min(totalPages, currentPage + neighborCount);
    return Array.from({ length: end - currentPage }, (_, index) => currentPage + index + 1);
  }, [currentPage, neighborCount, totalPages]);

  const goToPage = (nextPage: number) => {
    const page = Math.max(1, Math.min(totalPages, nextPage));
    if (page !== currentPage) {
      onPageChange(page);
    }
  };

  const submitInput = () => {
    if (!inputValue.trim()) {
      setInputValue(String(currentPage));
      return;
    }

    const parsed = Number(inputValue);
    if (Number.isFinite(parsed)) {
      goToPage(Math.trunc(parsed));
    } else {
      setInputValue(String(currentPage));
    }
  };

  return (
    <div className={`pagination-controls pager-controls ${className}`.trim()}>
      <button
        type="button"
        onClick={() => goToPage(1)}
        disabled={disabled || currentPage === 1}
        className="pagination-button"
        title="Go to first page"
        aria-label="Go to first page"
      >
        |&lt;&lt;
      </button>
      <button
        type="button"
        onClick={() => goToPage(currentPage - 1)}
        disabled={disabled || currentPage === 1}
        className="pagination-button"
        title="Previous page"
        aria-label="Previous page"
      >
        &lt;
      </button>

      <div className="pager-page-list">
        {previousPages.map((page) => (
          <button
            key={`prev-${page}`}
            type="button"
            onClick={() => goToPage(page)}
            disabled={disabled}
            className="pagination-button pager-page-number"
          >
            {page}
          </button>
        ))}
      </div>

      <div className="pager-current">
        <label htmlFor={inputId} className="sr-only">
          Jump to page
        </label>
        <input
          id={inputId}
          type="number"
          min={1}
          max={totalPages}
          value={inputValue}
          onChange={(event) => setInputValue(event.target.value)}
          onBlur={submitInput}
          onKeyDown={(event) => {
            if (event.key === 'Enter') {
              submitInput();
            }
          }}
          disabled={disabled}
          className="pager-input"
          aria-label="Jump to page"
        />
      </div>

      <div className="pager-page-list">
        {nextPages.map((page) => (
          <button
            key={`next-${page}`}
            type="button"
            onClick={() => goToPage(page)}
            disabled={disabled}
            className="pagination-button pager-page-number"
          >
            {page}
          </button>
        ))}
      </div>

      <button
        type="button"
        onClick={() => goToPage(currentPage + 1)}
        disabled={disabled || currentPage === totalPages}
        className="pagination-button"
        title="Next page"
        aria-label="Next page"
      >
        &gt;
      </button>
      <button
        type="button"
        onClick={() => goToPage(totalPages)}
        disabled={disabled || currentPage === totalPages}
        className="pagination-button"
        title="Go to last page"
        aria-label="Go to last page"
      >
        &gt;&gt;|
      </button>

      <div className="pagination-info">Page {currentPage} of {totalPages}{infoText ? ` (${infoText})` : ''}</div>
    </div>
  );
}
