import { useEffect, useRef } from 'react';
import type { TranscriptUpdate } from '../types';

interface TranscriptPanelProps {
  transcripts: TranscriptUpdate[];
}

const SPEAKER_META: Record<string, { name: string; color: string }> = {
  sales: {
    name: 'You',
    color: 'text-speaker-sales',
  },
  customer: {
    name: 'Customer',
    color: 'text-speaker-customer',
  },
};

function previousFinalSpeaker(transcripts: TranscriptUpdate[], index: number) {
  for (let i = index - 1; i >= 0; i--) {
    if (transcripts[i].is_final) return transcripts[i].speaker;
  }
  return '';
}

function EmptyState() {
  return (
    <div className="max-w-sm pt-2">
      <p className="text-sm font-medium text-ink">No transcript yet</p>
      <p className="text-sm text-hush mt-1.5 leading-relaxed">
        Start the mic or run a demo. What gets said on the call shows up here as it lands.
      </p>
    </div>
  );
}

export function TranscriptPanel({ transcripts }: TranscriptPanelProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const transcriptCount = transcripts.length;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [transcriptCount]);

  return (
    <div className="flex flex-col h-full min-h-0">
      <div className="px-4 sm:px-5 pt-4 pb-3 border-b border-rule/70 shrink-0">
        <h2 className="text-sm font-semibold text-ink">Call</h2>
        <p className="text-[13px] text-hush mt-0.5">Live transcript</p>
      </div>

      <div className="flex-1 overflow-y-auto px-4 sm:px-5 py-4">
        {transcripts.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="space-y-0.5">
            {transcripts.map((t, i) => {
              const meta = SPEAKER_META[t.speaker];
              const showLabel =
                Boolean(meta) &&
                t.is_final &&
                t.speaker !== previousFinalSpeaker(transcripts, i);

              return (
                <div key={`${t.timestamp}-${i}`} className={showLabel ? 'mt-5 first:mt-0' : undefined}>
                  {showLabel && meta && (
                    <p className={`text-[12px] font-semibold mb-1 ${meta.color}`}>
                      {meta.name}
                    </p>
                  )}
                  <p
                    className={`text-[14px] sm:text-[15px] leading-relaxed ${
                      t.is_final
                        ? t.speaker === 'customer'
                          ? 'text-ink'
                          : 'text-hush'
                        : 'text-quiet italic'
                    }`}
                  >
                    {t.text}
                    {!t.is_final && (
                      <span
                        className="inline-block w-0.5 h-3.5 bg-quiet ml-0.5 align-middle animate-blink"
                        aria-hidden="true"
                      />
                    )}
                  </p>
                </div>
              );
            })}
          </div>
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
