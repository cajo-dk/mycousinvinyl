/**
 * Activity status bar for real-time system updates.
 */

import { useEffect, useRef, useState } from 'react';
import { useMsal } from '@azure/msal-react';
import { apiRequest } from '@/auth/authConfig';
import { getEnv } from '@/config/runtimeEnv';
import { formatDateTime } from '@/utils/format';
import './ActivityStatusBar.css';

interface ActivityPayload {
  occurred_at?: string;
  user_name?: string | null;
  user_email?: string | null;
  user_id?: string | null;
  entity_id?: string | null;
  pressing_id?: string | null;
  album_id?: string | null;
  operation?: string;
  entity_type?: string;
  summary?: string;
}

const DISPLAY_MS = 20000;
const FADE_MS = 2000;

function toWebSocketUrl(baseUrl: string): string {
  const trimmed = baseUrl.replace(/\/+$/, '');
  if (!trimmed || trimmed.startsWith('/')) {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${wsProtocol}//${window.location.host}`;
  }
  if (trimmed.startsWith('https://')) {
    return `wss://${trimmed.slice('https://'.length)}`;
  }
  if (trimmed.startsWith('http://')) {
    return `ws://${trimmed.slice('http://'.length)}`;
  }
  return `ws://${trimmed}`;
}

function formatMessage(payload: ActivityPayload): string {
  const timestamp = payload.occurred_at ? formatDateTime(payload.occurred_at) : '';
  const actor = payload.user_name || payload.user_email || payload.user_id || 'Unknown user';
  const operation = payload.operation || 'updated';
  const entity = payload.entity_type || 'item';
  if (entity === 'pressing_ownership') {
    const album = payload.summary || 'an album';
    if (operation === 'created') {
      return `${timestamp} - User ${actor} added album ${album} to their collection`;
    }
    if (operation === 'deleted') {
      return `${timestamp} - User ${actor} deleted album ${album} from their collection`;
    }
    return `${timestamp} - User ${actor} ${operation} album ${album}`;
  }
  if (entity === 'collection_item') {
    const album = payload.summary || 'an album';
    if (operation === 'created') {
      return `${timestamp} - User ${actor} added album ${album} to their collection`;
    }
    if (operation === 'deleted') {
      return `${timestamp} - User ${actor} deleted album ${album} from their collection`;
    }
    return `${timestamp} - User ${actor} ${operation} album ${album}`;
  }

  const summary = payload.summary ? ` ${payload.summary}` : '';
  return `${timestamp} - User ${actor} ${operation} ${entity}${summary}`;
}

export function ActivityStatusBar() {
  const { instance, accounts } = useMsal();
  const [message, setMessage] = useState<string | null>(null);
  const [visible, setVisible] = useState(false);
  const [fading, setFading] = useState(false);
  const fadeTimer = useRef<number | null>(null);
  const hideTimer = useRef<number | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const clearTimers = () => {
    if (fadeTimer.current) window.clearTimeout(fadeTimer.current);
    if (hideTimer.current) window.clearTimeout(hideTimer.current);
    fadeTimer.current = null;
    hideTimer.current = null;
  };

  const showMessage = (text: string) => {
    clearTimers();
    setMessage(text);
    setVisible(false);
    setFading(false);

    requestAnimationFrame(() => {
      setVisible(true);
    });

    fadeTimer.current = window.setTimeout(() => setFading(true), DISPLAY_MS - FADE_MS);
    hideTimer.current = window.setTimeout(() => {
      setVisible(false);
      setMessage(null);
      setFading(false);
    }, DISPLAY_MS);
  };

  useEffect(() => {
    let reconnectTimer: number | null = null;

    const connect = async () => {
      if (accounts.length === 0) return;

      const response = await instance.acquireTokenSilent({
        ...apiRequest,
        account: accounts[0],
      });

      const baseUrl = getEnv('VITE_API_URL') || '';
      const wsUrl = `${toWebSocketUrl(baseUrl)}/ws/activity?access_token=${encodeURIComponent(response.accessToken)}`;

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload?.entity_type === 'pressing_ownership') {
            const pressingId = payload?.pressing_id || payload?.entity_id;
            const albumId = payload?.album_id;
            window.dispatchEvent(new CustomEvent('pressing-owners-changed', {
              detail: pressingId ? { pressingId } : { refreshAll: true }
            }));
            if (albumId) {
              window.dispatchEvent(new CustomEvent('album-owners-changed', {
                detail: { albumId }
              }));
            }
          }
          if (payload?.entity_type === 'collection_item') {
            const pressingId = payload?.pressing_id;
            window.dispatchEvent(new CustomEvent('pressing-owners-changed', {
              detail: pressingId ? { pressingId } : { refreshAll: true }
            }));
          }
          showMessage(formatMessage(payload));
        } catch {
          showMessage(event.data);
        }
      };

      ws.onclose = () => {
        if (reconnectTimer) window.clearTimeout(reconnectTimer);
        reconnectTimer = window.setTimeout(connect, 5000);
      };
    };

    connect();

    return () => {
      if (wsRef.current) wsRef.current.close();
      if (reconnectTimer) window.clearTimeout(reconnectTimer);
      clearTimers();
    };
  }, [instance, accounts]);

  return (
    <div className="activity-status-bar">
      <span
        className={`activity-status-text ${visible ? 'is-visible' : ''} ${fading ? 'fade-out' : ''}`}
      >
        {message || ''}
      </span>
    </div>
  );
}
