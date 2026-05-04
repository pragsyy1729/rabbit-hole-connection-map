import { useState } from 'react';

interface Props {
  onSubmit: (conceptA: string, conceptB: string) => void;
  isLoading: boolean;
  hasApiKey: boolean;
  onOpenSettings: () => void;
}

export default function InputForm({ onSubmit, isLoading, hasApiKey, onOpenSettings }: Props) {
  const [conceptA, setConceptA] = useState('');
  const [conceptB, setConceptB] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (conceptA.trim() && conceptB.trim()) {
      onSubmit(conceptA.trim(), conceptB.trim());
    }
  };

  return (
    <form className="input-form" onSubmit={handleSubmit}>
      <div className="input-form__row">
        <div className="input-form__field">
          <label className="input-form__label">Concept A</label>
          <input
            className="input-form__input"
            type="text"
            value={conceptA}
            onChange={(e) => setConceptA(e.target.value)}
            placeholder="e.g. Quantum Computing"
            disabled={isLoading}
          />
        </div>

        <div className="input-form__divider">→</div>

        <div className="input-form__field">
          <label className="input-form__label">Concept B</label>
          <input
            className="input-form__input"
            type="text"
            value={conceptB}
            onChange={(e) => setConceptB(e.target.value)}
            placeholder="e.g. Ancient Egyptian Pyramids"
            disabled={isLoading}
          />
        </div>
      </div>

      <div className="input-form__actions">
        {!hasApiKey && (
          <p className="input-form__warning">
            ⚠ No API key set.{' '}
            <button type="button" className="link-btn" onClick={onOpenSettings}>
              Add your NVIDIA key
            </button>{' '}
            to enable searches.
          </p>
        )}
        <button
          className="btn btn--primary btn--large"
          type="submit"
          disabled={isLoading || !conceptA.trim() || !conceptB.trim() || !hasApiKey}
        >
          {isLoading ? '⏳ Searching the rabbit hole…' : '🐇 Go Down the Rabbit Hole'}
        </button>
      </div>
    </form>
  );
}
