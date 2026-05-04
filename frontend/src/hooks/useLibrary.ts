import { useState, useEffect, useCallback } from 'react';
import type { RabbitHole } from '../types';

const API = 'http://localhost:8000';
const LS_KEY = 'rabbit_hole_library';

export function useLibrary() {
  const [library, setLibrary] = useState<RabbitHole[]>([]);

  const fetchLibrary = useCallback(async () => {
    try {
      const res = await fetch(`${API}/library`);
      const data = await res.json();
      setLibrary(data.entries ?? []);
      localStorage.setItem(LS_KEY, JSON.stringify(data.entries ?? []));
    } catch {
      const cached = localStorage.getItem(LS_KEY);
      if (cached) setLibrary(JSON.parse(cached));
    }
  }, []);

  useEffect(() => { fetchLibrary(); }, [fetchLibrary]);

  const deleteEntry = useCallback(async (id: string) => {
    await fetch(`${API}/library/${id}`, { method: 'DELETE' });
    await fetchLibrary();
  }, [fetchLibrary]);

  const exportLibrary = useCallback(() => {
    const blob = new Blob([JSON.stringify(library, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'knowledge_graph.json';
    a.click();
    URL.revokeObjectURL(url);
  }, [library]);

  const importLibrary = useCallback(async (file: File) => {
    const text = await file.text();
    const entries = JSON.parse(text);
    await fetch(`${API}/import`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ entries }),
    });
    await fetchLibrary();
  }, [fetchLibrary]);

  return { library, fetchLibrary, deleteEntry, exportLibrary, importLibrary };
}
