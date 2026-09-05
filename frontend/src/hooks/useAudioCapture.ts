import { useCallback, useEffect, useRef, useState } from 'react';

const TARGET_SAMPLE_RATE = 16000;

interface UseAudioCaptureOptions {
  onAudioData: (chunk: ArrayBuffer) => void;
}

export function useAudioCapture({ onAudioData }: UseAudioCaptureOptions) {
  const [isCapturing, setIsCapturing] = useState(false);
  const streamRef = useRef<MediaStream | null>(null);
  const contextRef = useRef<AudioContext | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);

  const captureRequest = useRef<object | null>(null);

  const stopCapture = useCallback(() => {
    captureRequest.current = null;
    if (processorRef.current) processorRef.current.onaudioprocess = null;
    processorRef.current?.disconnect();
    processorRef.current = null;

    void contextRef.current?.close().catch(() => {});
    contextRef.current = null;

    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;

    setIsCapturing(false);
  }, []);

  useEffect(() => stopCapture, [stopCapture]);

  const startCapture = useCallback(async () => {
    if (captureRequest.current) return;
    const request = {};
    captureRequest.current = request;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      if (captureRequest.current !== request) {
        stream.getTracks().forEach((track) => track.stop());
        return;
      }
      streamRef.current = stream;

      const context = new AudioContext({ sampleRate: TARGET_SAMPLE_RATE });
      contextRef.current = context;

      const source = context.createMediaStreamSource(stream);
      const processor = context.createScriptProcessor(4096, 1, 1);
      processorRef.current = processor;

      processor.onaudioprocess = (e) => {
        const float32 = e.inputBuffer.getChannelData(0);
        const int16 = new Int16Array(float32.length);
        for (let i = 0; i < float32.length; i++) {
          const s = Math.max(-1, Math.min(1, float32[i]));
          int16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
        }
        onAudioData(int16.buffer);
      };

      source.connect(processor);
      processor.connect(context.destination);
      setIsCapturing(true);
    } catch (err) {
      if (captureRequest.current === request) stopCapture();
      console.error('Failed to start audio capture:', err);
    }
  }, [onAudioData, stopCapture]);

  return { startCapture, stopCapture, isCapturing };
}
