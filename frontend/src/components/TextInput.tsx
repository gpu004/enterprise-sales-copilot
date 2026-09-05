import { useState, type FormEvent } from 'react';

interface TextInputProps {
  onSend: (text: string) => void;
  disabled?: boolean;
}

export function TextInput({ onSend, disabled = false }: TextInputProps) {
  const [value, setValue] = useState('');

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (disabled) return;
    const trimmed = value.trim();
    if (!trimmed) return;
    onSend(trimmed);
    setValue('');
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="px-3 sm:px-5 pb-4 pt-1 flex gap-2 sm:gap-3 shrink-0"
      aria-label="Send a customer question"
    >
      <div className="flex-1 min-w-0">
        <label htmlFor="question-input" className="sr-only">
          Customer question
        </label>
        <input
          id="question-input"
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder={disabled ? 'Connect to try a question…' : 'Try a customer question without the mic…'}
          disabled={disabled}
          autoComplete="off"
          className="w-full min-h-[44px] rounded-md border border-rule bg-sheet-raised px-3.5 py-2.5 text-sm text-ink placeholder:text-quiet transition-colors focus:outline-none focus:ring-2 focus:ring-mark/25 focus:border-mark disabled:opacity-50 disabled:cursor-not-allowed"
        />
      </div>
      <button
        type="submit"
        disabled={disabled || !value.trim()}
        className="min-h-[44px] px-4 sm:px-5 bg-ink text-sheet-raised text-sm font-semibold rounded-md hover:bg-ink/90 transition-colors cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed shrink-0"
      >
        Ask
      </button>
    </form>
  );
}
