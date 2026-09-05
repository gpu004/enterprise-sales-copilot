import type { SuggestionCard as SuggestionCardType } from '../types';

interface SuggestionCardProps {
  card: SuggestionCardType;
  isPinned: boolean;
  onDismiss: (id: string) => void;
  onTogglePin: (id: string) => void;
  isNewest?: boolean;
}

function confidenceLabel(confidence: number) {
  if (confidence > 0.8) return { text: 'Strong match', tone: 'text-live' };
  if (confidence >= 0.5) return { text: 'Partial match', tone: 'text-mid' };
  return { text: 'Weak match', tone: 'text-low' };
}

export function SuggestionCard({
  card,
  isPinned,
  onDismiss,
  onTogglePin,
  isNewest = false,
}: SuggestionCardProps) {
  const conf = confidenceLabel(card.confidence);
  const pct = Math.round(card.confidence * 100);

  return (
    <article
      className={`relative pl-4 sm:pl-5 ${isNewest ? 'animate-cue-in' : ''}`}
    >
      <div
        className={`absolute left-0 top-1 bottom-1 w-[3px] rounded-full ${
          isPinned ? 'bg-live' : 'bg-mark'
        }`}
        aria-hidden="true"
      />

      <div className="flex items-start justify-between gap-3 mb-2">
        <p className="text-[13px] text-hush leading-snug flex-1 pt-0.5">
          {card.question}
        </p>
        <div className="flex items-center shrink-0 -mt-1 -mr-1">
          <button
            onClick={() => onTogglePin(card.id)}
            className={`min-w-[40px] min-h-[40px] flex items-center justify-center rounded-md cursor-pointer transition-colors ${
              isPinned
                ? 'text-live bg-live-soft'
                : 'text-quiet hover:text-ink hover:bg-desk'
            }`}
            aria-label={isPinned ? 'Unpin answer' : 'Pin answer'}
            aria-pressed={isPinned}
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
              <path d="M10 2a1 1 0 011 1v1.323l3.954 1.582 1.599-.8a1 1 0 01.894 1.79l-1.233.616 1.738 5.42a1 1 0 01-.285 1.05A3.989 3.989 0 0115 15a3.989 3.989 0 01-2.667-1.019 1 1 0 01-.285-1.05l1.715-5.349L11 6.477V16h2a1 1 0 110 2H7a1 1 0 110-2h2V6.477L6.237 7.582l1.715 5.349a1 1 0 01-.285 1.05A3.989 3.989 0 015 15a3.989 3.989 0 01-2.667-1.019 1 1 0 01-.285-1.05l1.738-5.42-1.233-.617a1 1 0 01.894-1.788l1.599.799L9 4.323V3a1 1 0 011-1z" />
            </svg>
          </button>
          <button
            onClick={() => onDismiss(card.id)}
            className="min-w-[40px] min-h-[40px] flex items-center justify-center rounded-md text-quiet hover:text-ink hover:bg-desk cursor-pointer transition-colors"
            aria-label="Dismiss answer"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </button>
        </div>
      </div>

      <p className="font-serif text-[1.2rem] sm:text-[1.35rem] leading-[1.4] text-ink tracking-[-0.01em]">
        {card.answer}
      </p>

      <div className="flex items-center flex-wrap gap-x-4 gap-y-1 mt-3 text-[12px]">
        <span className="font-medium text-mark">{card.source}</span>
        <span className={`tabular-nums ${conf.tone}`} title={conf.text}>
          {conf.text} ({pct}%)
        </span>
      </div>
    </article>
  );
}
