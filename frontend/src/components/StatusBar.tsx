import { useEffect, useState } from 'react';

interface StatusBarProps {
  isConnected: boolean;
  isCapturing: boolean;
  isDemoRunning: boolean;
  onToggleMic: () => void;
  onStartDemo: () => void;
  onStopDemo: () => void;
}

function MicIcon({ className }: { className?: string }) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className={className} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M12 14a3 3 0 003-3V5a3 3 0 00-6 0v6a3 3 0 003 3z" />
      <path d="M19 11a1 1 0 10-2 0 5 5 0 01-10 0 1 1 0 10-2 0 7 7 0 006 6.93V20H8a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07A7 7 0 0019 11z" />
    </svg>
  );
}

function PlayIcon({ className }: { className?: string }) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className={className} viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
    </svg>
  );
}

function StopIcon({ className }: { className?: string }) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className={className} viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 00-1 1v4a1 1 0 001 1h4a1 1 0 001-1V8a1 1 0 00-1-1H8z" clipRule="evenodd" />
    </svg>
  );
}

function LiveTimer({ label }: { label: string }) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => setElapsed((e) => e + 1), 1000);
    return () => clearInterval(interval);
  }, []);

  const mins = Math.floor(elapsed / 60);
  const secs = elapsed % 60;
  const timer = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;

  return (
    <span
      className="inline-flex items-center gap-1.5 text-[13px] font-medium text-live tabular-nums"
      role="status"
      aria-live="polite"
    >
      <span className="w-1.5 h-1.5 rounded-full bg-live animate-live-dot" aria-hidden="true" />
      {label} · {timer}
    </span>
  );
}

export function StatusBar({
  isConnected,
  isCapturing,
  isDemoRunning,
  onToggleMic,
  onStartDemo,
  onStopDemo,
}: StatusBarProps) {
  const isLive = isCapturing || isDemoRunning;

  return (
    <header className="px-4 sm:px-5 pt-4 pb-3 flex items-end justify-between shrink-0 gap-4">
      <div className="min-w-0">
        <div className="flex items-baseline gap-3 flex-wrap">
          <h1 className="text-[1.6rem] sm:text-[1.75rem] font-semibold tracking-tight text-ink leading-none">
            Sales Copilot
          </h1>
          {isLive ? (
            <LiveTimer label={isCapturing ? 'Listening' : 'Demo'} />
          ) : (
            <span
              className="inline-flex items-center gap-1.5 text-[13px] text-quiet"
              role="status"
              aria-live="polite"
            >
              <span
                className={`w-1.5 h-1.5 rounded-full ${isConnected ? 'bg-live/50' : 'bg-stop animate-blink'}`}
                aria-hidden="true"
              />
              {isConnected ? 'Ready' : 'Offline'}
            </span>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2 shrink-0">
        {isDemoRunning ? (
          <button
            onClick={onStopDemo}
            className="flex items-center gap-1.5 min-h-[40px] px-3 py-2 rounded-md text-sm font-medium cursor-pointer bg-stop text-white hover:bg-stop/90 transition-colors"
            aria-label="Stop demo playback"
          >
            <StopIcon className="w-4 h-4" />
            <span className="hidden sm:inline">Stop demo</span>
          </button>
        ) : (
          <button
            onClick={onStartDemo}
            disabled={!isConnected}
            className="flex items-center gap-1.5 min-h-[40px] px-3 py-2 rounded-md text-sm font-medium cursor-pointer bg-sheet-raised text-ink border border-rule hover:border-ink/25 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            aria-label="Start demo playback"
          >
            <PlayIcon className="w-4 h-4 text-mark" />
            <span className="hidden sm:inline">Run demo</span>
          </button>
        )}

        <button
          onClick={onToggleMic}
          disabled={!isConnected}
          className={`flex items-center gap-1.5 min-h-[40px] px-3.5 py-2 rounded-md text-sm font-semibold cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed transition-colors ${
            isCapturing
              ? 'bg-stop text-white hover:bg-stop/90 animate-pulse-ring'
              : 'bg-live text-white hover:bg-live/90'
          }`}
          aria-label={isCapturing ? 'Stop microphone capture' : 'Start microphone capture'}
          aria-pressed={isCapturing}
        >
          <MicIcon className="w-4 h-4" />
          <span className="hidden sm:inline">{isCapturing ? 'Stop mic' : 'Start mic'}</span>
        </button>
      </div>
    </header>
  );
}
