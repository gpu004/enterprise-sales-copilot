'use client';

import { useCallback } from 'react';
import { useSearchParams } from 'next/navigation';
import { useWebSocket } from './hooks/useWebSocket';
import { useAudioCapture } from './hooks/useAudioCapture';
import { StatusBar } from './components/StatusBar';
import { TranscriptPanel } from './components/TranscriptPanel';
import { SuggestionPanel } from './components/SuggestionPanel';
import { TextInput } from './components/TextInput';
import type { SuggestionCard, TranscriptUpdate } from './types';

const PREVIEW_TRANSCRIPTS: TranscriptUpdate[] = [
  {
    text: 'We already have life coverage through work, but I am worried about the gap if I leave.',
    is_final: true,
    speaker: 'customer',
    timestamp: '2026-01-01T00:00:01Z',
  },
  {
    text: 'That is a common concern. Let me check what a portable term policy would look like.',
    is_final: true,
    speaker: 'sales',
    timestamp: '2026-01-01T00:00:08Z',
  },
  {
    text: 'What is the monthly premium for a healthy 40-year-old on a 20-year term?',
    is_final: true,
    speaker: 'customer',
    timestamp: '2026-01-01T00:00:14Z',
  },
];

const PREVIEW_SUGGESTIONS: SuggestionCard[] = [
  {
    id: 'preview-1',
    question: 'What is the monthly premium for a healthy 40-year-old on a 20-year term?',
    answer:
      'For a healthy non-smoker at 40, our 20-year term starts around $28 a month for $500k. I can pull the exact quote for their age and state while we talk.',
    source: 'Pricing · Term Life',
    confidence: 0.91,
    timestamp: '2026-01-01T00:00:16Z',
  },
  {
    id: 'preview-2',
    question: 'Does employer life insurance stay with me if I leave?',
    answer:
      'Most group life coverage ends when employment ends. A portable individual term policy keeps the benefit in place through a job change.',
    source: 'FAQ · Life',
    confidence: 0.84,
    timestamp: '2026-01-01T00:00:10Z',
  },
];

export default function App() {
  const searchParams = useSearchParams();
  const preview = searchParams.get('preview') === '1';

  const {
    isConnected,
    transcripts,
    suggestions,
    isDemoRunning,
    sendAudio,
    sendText,
    dismissSuggestion,
    startDemo,
    stopDemo,
  } = useWebSocket();

  const { startCapture, stopCapture, isCapturing } = useAudioCapture({
    onAudioData: sendAudio,
  });

  const handleToggleMic = useCallback(() => {
    if (isCapturing) {
      stopCapture();
    } else {
      startCapture();
    }
  }, [isCapturing, startCapture, stopCapture]);

  const shownTranscripts =
    preview && transcripts.length === 0 ? PREVIEW_TRANSCRIPTS : transcripts;
  const shownSuggestions =
    preview && suggestions.length === 0 ? PREVIEW_SUGGESTIONS : suggestions;

  return (
    <div className="flex flex-col h-dvh">
      <StatusBar
        isConnected={isConnected}
        isCapturing={isCapturing}
        isDemoRunning={isDemoRunning}
        onToggleMic={handleToggleMic}
        onStartDemo={startDemo}
        onStopDemo={stopDemo}
      />

      <main className="flex flex-1 min-h-0 flex-col lg:flex-row gap-px bg-rule mx-3 mb-3 rounded-md overflow-hidden border border-rule shadow-[0_1px_0_rgb(27_40_56/0.04)]">
        <section
          className="flex flex-col min-h-[220px] lg:min-h-0 lg:w-[36%] xl:w-[32%] bg-sheet"
          aria-label="Live transcript"
        >
          <TranscriptPanel transcripts={shownTranscripts} />
        </section>

        <section
          className="flex flex-col flex-1 min-h-[280px] lg:min-h-0 bg-sheet-raised"
          aria-label="Speakable answers"
        >
          <SuggestionPanel
            suggestions={shownSuggestions}
            onDismiss={dismissSuggestion}
          />
        </section>
      </main>

      <TextInput onSend={sendText} disabled={!isConnected} />
    </div>
  );
}
