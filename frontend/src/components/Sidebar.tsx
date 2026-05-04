import { useRef } from 'react';
import type { RabbitHole } from '../types';
import LibraryList from './LibraryList';

interface Props {
  library: RabbitHole[];
  activeId: string | null;
  onSelect: (hole: RabbitHole) => void;
  onDelete: (id: string) => void;
  onExport: () => void;
  onImport: (file: File) => void;
  collapsed: boolean;
  onToggle: () => void;
}

export default function Sidebar({ library, activeId, onSelect, onDelete, onExport, onImport, collapsed, onToggle }: Props) {
  const fileRef = useRef<HTMLInputElement>(null);

  return (
    <aside className={`sidebar ${collapsed ? 'sidebar--collapsed' : ''}`}>
      <div className="sidebar__header">
        {!collapsed && <h2 className="sidebar__title">📚 Rabbit Holes</h2>}
        <button className="sidebar__toggle" onClick={onToggle} title={collapsed ? 'Expand' : 'Collapse'}>
          {collapsed ? '›' : '‹'}
        </button>
      </div>

      {!collapsed && (
        <>
          <div className="sidebar__body">
            <LibraryList
              library={library}
              activeId={activeId}
              onSelect={onSelect}
              onDelete={onDelete}
            />
          </div>

          <div className="sidebar__footer">
            <button className="btn btn--secondary btn--sm" onClick={onExport}>
              ↓ Export JSON
            </button>
            <button className="btn btn--secondary btn--sm" onClick={() => fileRef.current?.click()}>
              ↑ Import JSON
            </button>
            <input
              ref={fileRef}
              type="file"
              accept=".json"
              style={{ display: 'none' }}
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) onImport(file);
                e.target.value = '';
              }}
            />
          </div>
        </>
      )}
    </aside>
  );
}
