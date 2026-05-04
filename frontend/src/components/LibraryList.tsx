import type { RabbitHole } from '../types';

interface Props {
  library: RabbitHole[];
  activeId: string | null;
  onSelect: (hole: RabbitHole) => void;
  onDelete: (id: string) => void;
}

export default function LibraryList({ library, activeId, onSelect, onDelete }: Props) {
  if (library.length === 0) {
    return (
      <p className="library__empty">No rabbit holes saved yet. Go explore!</p>
    );
  }

  return (
    <ul className="library__list">
      {library.map((hole) => (
        <li
          key={hole.id}
          className={`library__item ${hole.id === activeId ? 'library__item--active' : ''}`}
          onClick={() => onSelect(hole)}
        >
          <div className="library__item-title">
            {hole.concept_a} → {hole.concept_b}
          </div>
          <div className="library__item-meta">
            {hole.steps.length} steps &bull; {new Date(hole.created_at).toLocaleDateString()}
          </div>
          <button
            className="library__delete"
            onClick={(e) => { e.stopPropagation(); onDelete(hole.id); }}
            title="Delete"
          >
            ×
          </button>
        </li>
      ))}
    </ul>
  );
}
