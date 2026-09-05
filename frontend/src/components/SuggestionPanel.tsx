import { useState, useCallback } from 'react';
import type { SuggestionCard as SuggestionCardType } from '../types';
import { SuggestionCard } from './SuggestionCard';

interface SuggestionPanelProps {
  suggestions: SuggestionCardType[];
  onDismiss: (id: string) => void;
}

function EmptyState() {
  return (
    <div className="px-1 pt-2 sm:pt-4 max-w-lg">
      <p className="font-serif text-[1.65rem] sm:text-[1.85rem] text-ink leading-[1.25] tracking-tight">
        When the customer asks about a product, a short reply shows up here.
      </p>
      <p className="text-sm text-hush mt-4 leading-relaxed max-w-sm">
        Say it on the call, or pin it so it stays while you take the next question.
      </p>
    </div>
  );
}

export function SuggestionPanel({ suggestions, onDismiss }: SuggestionPanelProps) {
  const [pinnedIds, setPinnedIds] = useState<Set<string>>(new Set());

  const togglePin = useCallback((id: string) => {
    setPinnedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  const pinned = suggestions.filter((s) => pinnedIds.has(s.id));
  const unpinned = suggestions.filter((s) => !pinnedIds.has(s.id));
  const sorted = [...pinned, ...unpinned];

  return (
    <div className="flex flex-col h-full min-h-0">
      <div className="px-4 sm:px-6 pt-4 pb-3 border-b border-rule/60 flex items-end justify-between gap-3 shrink-0">
        <div>
          <h2 className="font-serif text-base font-medium text-ink tracking-tight">What to say</h2>
          <p className="text-[13px] text-hush mt-0.5">Product answers for this call</p>
        </div>
        {sorted.length > 0 && (
          <span className="text-[12px] tabular-nums text-hush shrink-0">
            {sorted.length} {sorted.length === 1 ? 'cue' : 'cues'}
          </span>
        )}
      </div>

      <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-5 sm:py-6">
        {sorted.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="space-y-6">
            {pinned.length > 0 && unpinned.length > 0 && (
              <p className="text-[12px] font-medium text-hush">Pinned</p>
            )}
            {sorted.map((card, index) => {
              const showUnpinnedHeader =
                pinned.length > 0 &&
                unpinned.length > 0 &&
                index === pinned.length;

              return (
                <div key={card.id}>
                  {showUnpinnedHeader && (
                    <p className="text-[12px] font-medium text-hush mb-3 mt-1">Earlier</p>
                  )}
                  <SuggestionCard
                    card={card}
                    isPinned={pinnedIds.has(card.id)}
                    onDismiss={onDismiss}
                    onTogglePin={togglePin}
                    isNewest={index === 0 && !pinnedIds.has(card.id)}
                  />
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
