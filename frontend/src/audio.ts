/** Decode base64 MP3 and settle when playback ends, fails, or is cancelled. */
export function playAudio(
  base64Audio: string,
  speaker?: string,
  signal?: AbortSignal,
): Promise<void> {
  return new Promise((resolve) => {
    if (signal?.aborted) return resolve();
    let url: string | undefined;
    let audio: HTMLAudioElement | undefined;
    const finish = () => {
      signal?.removeEventListener('abort', finish);
      if (audio) {
        audio.onended = null;
        audio.onerror = null;
        audio.pause();
        audio.removeAttribute('src');
        audio.load();
      }
      if (url) URL.revokeObjectURL(url);
      audio = undefined;
      url = undefined;
      resolve();
    };
    try {
      const byteString = atob(base64Audio);
      const bytes = Uint8Array.from(byteString, (char) => char.charCodeAt(0));
      url = URL.createObjectURL(new Blob([bytes], { type: 'audio/mpeg' }));
      audio = new Audio(url);
      if (speaker === 'customer') audio.playbackRate = 1.15;
      audio.onended = finish;
      audio.onerror = finish;
      signal?.addEventListener('abort', finish, { once: true });
      audio.play().catch(finish);
    } catch {
      finish();
    }
  });
}
