import { useEffect, useRef } from 'react';
import type { RabbitHole } from '../types';

export function useSSE(onPathUpdate: (hole: RabbitHole) => void) {
  const esRef = useRef<EventSource | null>(null);
  const retryRef = useRef(0);

  useEffect(() => {
    function connect() {
      const es = new EventSource('http://localhost:8000/events');
      esRef.current = es;

      es.onmessage = (e) => {
        try {
          const event = JSON.parse(e.data);
          if (event.type === 'path_update') {
            retryRef.current = 0;
            onPathUpdate(event.data as RabbitHole);
          }
        } catch {
          // ignore malformed events
        }
      };

      es.onerror = () => {
        es.close();
        const delay = Math.min(1000 * 2 ** retryRef.current, 30000);
        retryRef.current += 1;
        setTimeout(connect, delay);
      };
    }

    connect();
    return () => esRef.current?.close();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
}
