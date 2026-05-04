import { useState } from 'react';

interface Props {
  apiKey: string;
  onSave: (key: string) => void;
  onClose: () => void;
}

export default function SettingsModal({ apiKey, onSave, onClose }: Props) {
  const [draft, setDraft] = useState(apiKey);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2 className="modal__title">Settings</h2>

        <label className="modal__label">
          NVIDIA NIM API Key
          <input
            className="modal__input"
            type="password"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="nvapi-..."
            autoFocus
          />
        </label>
        <p className="modal__hint">
          Stored locally in your browser. Never sent to any server other than NVIDIA.
        </p>

        <div className="modal__actions">
          <button className="btn btn--secondary" onClick={onClose}>Cancel</button>
          <button
            className="btn btn--primary"
            onClick={() => { onSave(draft); onClose(); }}
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
}
