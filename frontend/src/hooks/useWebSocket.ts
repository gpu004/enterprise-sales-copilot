import { useCallback, useEffect, useRef, useState } from 'react';
import { playAudio } from '../audio';
import type { TranscriptUpdate, SuggestionCard, WSMessage } from '../types';

const MAX_RECONNECT_DELAY = 30000;
const INITIAL_RECONNECT_DELAY = 1000;

type Endpoint = 'session' | 'demo';

function wsSend(ws: WebSocket | null, msg: object) {
  if (ws?.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(msg));
  }
}

/** Resolve WS base URL: NEXT_PUBLIC_BACKEND_URL in prod; local FastAPI in dev. */
function backendWsBase(): string {
  const configured = process.env.NEXT_PUBLIC_BACKEND_URL?.replace(/\/$/, '');
  if (configured) {
    if (configured.startsWith('https://')) return configured.replace(/^https/, 'wss');
    if (configured.startsWith('http://')) return configured.replace(/^http/, 'ws');
    return configured;
  }
  // Next.js does not proxy WebSockets reliably — talk to FastAPI directly in dev.
  if (process.env.NODE_ENV === 'development') {
    return 'ws://localhost:8000';
  }
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}`;
}

function applyTranscript(
  prev: TranscriptUpdate[],
  update: TranscriptUpdate,
): TranscriptUpdate[] {
  if (prev.length > 0 && !prev[prev.length - 1].is_final) {
    return [...prev.slice(0, -1), update];
  }
  return [...prev, update];
}

export function useWebSocket() {
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [transcripts, setTranscripts] = useState<TranscriptUpdate[]>([]);
  const [suggestions, setSuggestions] = useState<SuggestionCard[]>([]);
  const [isDemoRunning, setIsDemoRunning] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectDelay = useRef(INITIAL_RECONNECT_DELAY);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>(undefined);
  const mountedRef = useRef(true);
  const endpointRef = useRef<Endpoint>('session');
  const playbackRef = useRef<AbortController | null>(null);

  const connect = useCallback(function connect(endpoint: Endpoint = 'session') {
    if (!mountedRef.current || wsRef.current) return;
    endpointRef.current = endpoint;

    const wsPath = endpoint === 'demo' ? '/ws/demo' : '/ws/session';
    const ws = new WebSocket(`${backendWsBase()}${wsPath}`);

    let playbackDone = Promise.resolve();

    ws.onopen = () => {
      if (!mountedRef.current || wsRef.current !== ws) return;
      setIsConnected(true);
      reconnectDelay.current = INITIAL_RECONNECT_DELAY;
    };

    ws.onmessage = (event) => {
      if (!mountedRef.current || wsRef.current !== ws) return;
      try {
        const msg = JSON.parse(event.data) as WSMessage;
        switch (msg.type) {
          case 'transcript_update':
            setTranscripts((prev) => applyTranscript(prev, msg.payload));
            break;
          case 'suggestion_card':
            setSuggestions((prev) => [msg.payload, ...prev]);
            break;
          case 'audio_play': {
            if (msg.payload.audio && endpoint === 'demo') {
              playbackRef.current?.abort();
              const playback = new AbortController();
              playbackRef.current = playback;
              playbackDone = playAudio(msg.payload.audio, msg.payload.speaker, playback.signal);
            }
            break;
          }
          case 'error':
            setError(msg.payload.message);
            break;
          case 'status':
            if (msg.payload.message === 'turn_complete' && endpoint === 'demo') {
              void playbackDone.then(() => {
                if (mountedRef.current && wsRef.current === ws) {
                  wsSend(ws, { type: 'demo_next' });
                }
              });
            }
            if (msg.payload.message === 'demo_started') {
              setIsDemoRunning(true);
              wsSend(ws, { type: 'demo_next' });
            }
            if (msg.payload.message === 'demo_ended') {
              setIsDemoRunning(false);
              endpointRef.current = 'session';
              ws.close();
            }
            break;
        }
      } catch {
        // ignore non-JSON messages
      }
    };

    ws.onclose = () => {
      if (!mountedRef.current || wsRef.current !== ws) return;
      setIsConnected(false);
      setIsDemoRunning(false);
      wsRef.current = null;

      playbackRef.current?.abort();

      if (endpointRef.current === 'session') {
        reconnectTimer.current = setTimeout(() => {
          reconnectDelay.current = Math.min(
            reconnectDelay.current * 2,
            MAX_RECONNECT_DELAY,
          );
          connect('session');
        }, reconnectDelay.current);
      }
    };

    ws.onerror = () => {
      ws.close();
    };

    wsRef.current = ws;
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    connect('session');
    return () => {
      mountedRef.current = false;
      clearTimeout(reconnectTimer.current);
      const ws = wsRef.current;
      wsRef.current = null;
      playbackRef.current?.abort();
      ws?.close();
    };
  }, [connect]);

  const sendAudio = useCallback((data: ArrayBuffer) => {
    if (endpointRef.current === 'session' && wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(data);
    }
  }, []);

  const sendText = useCallback((text: string) => {
    if (endpointRef.current === 'session' && wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'text_input', text }));
    }
  }, []);

  const dismissSuggestion = useCallback((id: string) => {
    setSuggestions((prev) => prev.filter((s) => s.id !== id));
  }, []);

  const switchEndpoint = useCallback(
    (endpoint: Endpoint) => {
      clearTimeout(reconnectTimer.current);
      setError(null);
      setTranscripts([]);
      setSuggestions([]);
      const ws = wsRef.current;
      wsRef.current = null;
      playbackRef.current?.abort();
      ws?.close();
      setIsConnected(false);
      connect(endpoint);
    },
    [connect],
  );

  const startDemo = useCallback(() => {
    setIsDemoRunning(true);
    switchEndpoint('demo');
  }, [switchEndpoint]);

  const stopDemo = useCallback(() => {
    setIsDemoRunning(false);
    switchEndpoint('session');
  }, [switchEndpoint]);

  return {
    error,
    isConnected,
    transcripts,
    suggestions,
    isDemoRunning,
    sendAudio,
    sendText,
    dismissSuggestion,
    startDemo,
    stopDemo,
  };
}
