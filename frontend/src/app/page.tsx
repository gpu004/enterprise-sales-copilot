import { Suspense } from 'react';
import App from '../App';

export default function Home() {
  return (
    <Suspense fallback={<div className="h-dvh bg-desk" />}>
      <App />
    </Suspense>
  );
}
