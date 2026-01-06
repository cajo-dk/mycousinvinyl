/**
 * Shared loader for album owners with batching and de-duplication.
 */

import { useEffect, useMemo, useRef, useState } from 'react';
import { collectionSharingApi } from '@/api/services';
import { UserOwnerInfo } from '@/types/api';

const CHUNK_SIZE = 200;

export function useAlbumOwners(albumIds: string[]) {
  const ownersRef = useRef<Record<string, UserOwnerInfo[]>>({});
  const requestedRef = useRef<Set<string>>(new Set());
  const queueRef = useRef<string[]>([]);
  const queuedRef = useRef<Set<string>>(new Set());
  const inFlightRef = useRef(false);
  const scheduledRef = useRef(false);
  const mountedRef = useRef(true);
  const pendingRefreshRef = useRef<Set<string>>(new Set());
  const [ownersByAlbum, setOwnersByAlbum] = useState<Record<string, UserOwnerInfo[]>>({});

  const uniqueIds = useMemo(() => Array.from(new Set(albumIds)), [albumIds]);
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
      chunk.forEach((albumId) => queuedRef.current.delete(albumId));
      pendingIds.push(...chunk);

      try {
        const response = await collectionSharingApi.getAlbumOwnersBatch(chunk);
        const ownersMap = response.owners_by_album || {};
        chunk.forEach((albumId) => {
          ownersRef.current[albumId] = ownersMap[albumId] || [];
        });
      } catch {
        chunk.forEach((albumId) => {
          requestedRef.current.delete(albumId);
        });
      }
    }

    if (mountedRef.current) {
      setOwnersByAlbum({ ...ownersRef.current });
    } else {
      pendingIds.forEach((albumId) => requestedRef.current.delete(albumId));
    }

    inFlightRef.current = false;

    if (pendingRefreshRef.current.size > 0) {
      const refreshIds: string[] = [];
      pendingRefreshRef.current.forEach((albumId) => {
        if (visibleSetRef.current.has(albumId)) {
          refreshIds.push(albumId);
        }
      });
      refreshIds.forEach((albumId) => {
        pendingRefreshRef.current.delete(albumId);
        if (!queuedRef.current.has(albumId)) {
          queuedRef.current.add(albumId);
          queueRef.current.push(albumId);
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
    uniqueIds.forEach((albumId) => {
      if (!requestedRef.current.has(albumId)) {
        requestedRef.current.add(albumId);
        newIds.push(albumId);
      }
    });

    if (newIds.length === 0) {
      return;
    }

    newIds.forEach((albumId) => {
      if (!queuedRef.current.has(albumId)) {
        queuedRef.current.add(albumId);
        queueRef.current.push(albumId);
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
    pendingRefreshRef.current.forEach((albumId) => {
      if (visibleSetRef.current.has(albumId)) {
        toRefresh.push(albumId);
      }
    });

    if (toRefresh.length === 0) {
      return;
    }

    toRefresh.forEach((albumId) => {
      pendingRefreshRef.current.delete(albumId);
      if (!queuedRef.current.has(albumId)) {
        queuedRef.current.add(albumId);
        queueRef.current.push(albumId);
      }
    });
    schedulePump();
  }, [uniqueIds]);

  useEffect(() => {
    const handler = (event: Event) => {
      const detail = (event as CustomEvent).detail as { albumId?: string; refreshAll?: boolean } | undefined;
      if (detail?.refreshAll) {
        const visibleIds = Array.from(visibleSetRef.current);
        if (visibleIds.length === 0) {
          return;
        }

        if (inFlightRef.current) {
          visibleIds.forEach((albumId) => pendingRefreshRef.current.add(albumId));
          return;
        }

        visibleIds.forEach((albumId) => {
          if (!queuedRef.current.has(albumId)) {
            queuedRef.current.add(albumId);
            queueRef.current.push(albumId);
          }
        });
        schedulePump();
        return;
      }

      const albumId = detail?.albumId;
      if (!albumId) {
        return;
      }

      if (!visibleSetRef.current.has(albumId)) {
        pendingRefreshRef.current.add(albumId);
        return;
      }

      if (inFlightRef.current || queuedRef.current.has(albumId)) {
        pendingRefreshRef.current.add(albumId);
        return;
      }

      if (!queuedRef.current.has(albumId)) {
        queuedRef.current.add(albumId);
        queueRef.current.push(albumId);
        schedulePump();
      }
    };

    window.addEventListener('album-owners-changed', handler as EventListener);
    return () => {
      window.removeEventListener('album-owners-changed', handler as EventListener);
    };
  }, [uniqueIds]);

  return ownersByAlbum;
}
