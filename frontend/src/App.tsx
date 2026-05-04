import { useState, useCallback } from 'react';
import type { RabbitHole } from './types';
import { useSSE } from './hooks/useSSE';
import { useLibrary } from './hooks/useLibrary';
import Sidebar from './components/Sidebar';
import InputForm from './components/InputForm';
import PathViewer from './components/PathViewer';
import SettingsModal from './components/SettingsModal';
import LoadingOverlay from './components/LoadingOverlay';

const API = 'http://localhost:8000';

export default function App() {
  const [apiKey, setApiKey] = useState(() => localStorage.getItem('nvidia_api_key') ?? '');
  const [showSettings, setShowSettings] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [currentHole, setCurrentHole] = useState<RabbitHole | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { library, fetchLibrary, deleteEntry, exportLibrary, importLibrary } = useLibrary();

  const handlePathUpdate = useCallback((hole: RabbitHole) => {
    setCurrentHole(hole);
    setIsLoading(false);
    fetchLibrary();
  }, [fetchLibrary]);

  useSSE(handlePathUpdate);

  const handleSubmit = async (conceptA: string, conceptB: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API}/find-path`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          concept_a: conceptA,
          concept_b: conceptB,
          nvidia_api_key: apiKey,
          steps: 4,
        }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail ?? 'Unknown error');
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Something went wrong');
      setIsLoading(false);
    }
  };

  const handleSaveApiKey = (key: string) => {
    setApiKey(key);
    localStorage.setItem('nvidia_api_key', key);
  };

  return (
    <div className="app">
      <header className="app__header">
        <div className="app__logo">🐇 Rabbit Hole Knowledge Mapper</div>
        <button className="btn btn--ghost" onClick={() => setShowSettings(true)}>
          ⚙ Settings
        </button>
      </header>

      <div className="app__body">
        <Sidebar
          library={library}
          activeId={currentHole?.id ?? null}
          onSelect={setCurrentHole}
          onDelete={deleteEntry}
          onExport={exportLibrary}
          onImport={importLibrary}
          collapsed={sidebarCollapsed}
          onToggle={() => setSidebarCollapsed((c) => !c)}
        />

        <main className="app__main">
          <InputForm
            onSubmit={handleSubmit}
            isLoading={isLoading}
            hasApiKey={!!apiKey}
            onOpenSettings={() => setShowSettings(true)}
          />

          {error && <div className="error-banner">⚠ {error}</div>}

          <PathViewer hole={currentHole} />
        </main>
      </div>

      {isLoading && <LoadingOverlay />}

      {showSettings && (
        <SettingsModal
          apiKey={apiKey}
          onSave={handleSaveApiKey}
          onClose={() => setShowSettings(false)}
        />
      )}
    </div>
  );
}
