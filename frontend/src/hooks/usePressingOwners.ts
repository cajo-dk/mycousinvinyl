/**
 * Shared loader for pressing owners with batching and de-duplication.
 */

import { useEffect, useMemo, useRef, useState } from 'react';
import { collectionSharingApi } from '@/api/services';
import { UserOwnerInfo } from '@/types/api';

const CHUNK_SIZE = 200;

export function usePressingOwners(pressingIds: string[]) {
  const ownersRef = useRef<Record<string, UserOwnerInfo[]>>({});
  const requestedRef = useRef<Set<string>>(new Set());
  const queueRef = useRef<string[]>([]);
  const queuedRef = useRef<Set<string>>(new Set());
  const inFlightRef = useRef(false);
  const scheduledRef = useRef(false);
  const mountedRef = useRef(true);
  const pendingRefreshRef = useRef<Set<string>>(new Set());
  const [ownersByPressing, setOwnersByPressing] = useState<Record<string, UserOwnerInfo[]>>({});

  const uniqueIds = useMemo(() => Array.from(new Set(pressingIds)), [pressingIds]);
  const visibleSetRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const schedulePump = () => {
    if (scheduledRef.current) return;
    scheduledRef.current = true;
    setTimeout(() => {
      scheduledRef.current = false;
      void pumpQueue();
    }, 0);
  };

  const pumpQueue = async () => {
    if (inFlightRef.current || queueRef.current.length === 0) {
      return;
    }

    inFlightRef.current = true;
    const pendingIds: string[] = [];

    while (queueRef.current.length > 0) {
      const chunk = queueRef.current.splice(0, CHUNK_SIZE);
      chunk.forEach((pressingId) => queuedRef.current.delete(pressingId));
      pendingIds.push(...chunk);

      try {
        const response = await collectionSharingApi.getPressingOwnersBatch(chunk);
        const ownersMap = response.owners_by_pressing || {};
        chunk.forEach((pressingId) => {
          ownersRef.current[pressingId] = ownersMap[pressingId] || [];
        });
      } catch {
        chunk.forEach((pressingId) => {
          requestedRef.current.delete(pressingId);
        });
      }
    }

    if (mountedRef.current) {
      setOwnersByPressing({ ...ownersRef.current });
    } else {
      pendingIds.forEach((pressingId) => requestedRef.current.delete(pressingId));
    }

    inFlightRef.current = false;

    if (pendingRefreshRef.current.size > 0) {
      const refreshIds: string[] = [];
      pendingRefreshRef.current.forEach((pressingId) => {
        if (visibleSetRef.current.has(pressingId)) {
          refreshIds.push(pressingId);
        }
      });
      refreshIds.forEach((pressingId) => {
        pendingRefreshRef.current.delete(pressingId);
        if (!queuedRef.current.has(pressingId)) {
          queuedRef.current.add(pressingId);
          queueRef.current.push(pressingId);
        }
      });
      if (refreshIds.length > 0) {
        schedulePump();
      }
    }

    if (queueRef.current.length > 0) {
      schedulePump();
    }
  };

  useEffect(() => {
    if (uniqueIds.length === 0) {
      return;
    }

    const newIds: string[] = [];
    uniqueIds.forEach((pressingId) => {
      if (!requestedRef.current.has(pressingId)) {
        requestedRef.current.add(pressingId);
        newIds.push(pressingId);
      }
    });

    if (newIds.length === 0) {
      return;
    }

    newIds.forEach((pressingId) => {
      if (!queuedRef.current.has(pressingId)) {
        queuedRef.current.add(pressingId);
        queueRef.current.push(pressingId);
      }
    });
    schedulePump();
  }, [uniqueIds]);

  useEffect(() => {
    visibleSetRef.current = new Set(uniqueIds);
    if (pendingRefreshRef.current.size === 0) {
      return;
    }

    const toRefresh: string[] = [];
    pendingRefreshRef.current.forEach((pressingId) => {
      if (visibleSetRef.current.has(pressingId)) {
        toRefresh.push(pressingId);
      }
    });

    if (toRefresh.length === 0) {
      return;
    }

    toRefresh.forEach((pressingId) => {
      pendingRefreshRef.current.delete(pressingId);
      if (!queuedRef.current.has(pressingId)) {
        queuedRef.current.add(pressingId);
        queueRef.current.push(pressingId);
      }
    });
    schedulePump();
  }, [uniqueIds]);

  useEffect(() => {
    const handler = (event: Event) => {
      const detail = (event as CustomEvent).detail as { pressingId?: string; refreshAll?: boolean } | undefined;
      if (detail?.refreshAll) {
        const visibleIds = Array.from(visibleSetRef.current);
        if (visibleIds.length === 0) {
          return;
        }

        if (inFlightRef.current) {
          visibleIds.forEach((pressingId) => pendingRefreshRef.current.add(pressingId));
          return;
        }

        visibleIds.forEach((pressingId) => {
          if (!queuedRef.current.has(pressingId)) {
            queuedRef.current.add(pressingId);
            queueRef.current.push(pressingId);
          }
        });
        schedulePump();
        return;
      }

      const pressingId = detail?.pressingId;
      if (!pressingId) {
        return;
      }

      if (!visibleSetRef.current.has(pressingId)) {
        pendingRefreshRef.current.add(pressingId);
        return;
      }

      if (inFlightRef.current || queuedRef.current.has(pressingId)) {
        pendingRefreshRef.current.add(pressingId);
        return;
      }

      if (!queuedRef.current.has(pressingId)) {
        queuedRef.current.add(pressingId);
        queueRef.current.push(pressingId);
        schedulePump();
      }
    };

    window.addEventListener('pressing-owners-changed', handler as EventListener);
    return () => {
      window.removeEventListener('pressing-owners-changed', handler as EventListener);
    };
  }, [uniqueIds]);

  return ownersByPressing;
}
