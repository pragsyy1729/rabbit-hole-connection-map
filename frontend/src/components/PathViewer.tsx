import type { RabbitHole } from '../types';
import PathCard from './PathCard';

interface Props {
  hole: RabbitHole | null;
}

export default function PathViewer({ hole }: Props) {
  if (!hole) {
    return (
      <div className="path-viewer--empty">
        <div className="path-viewer__placeholder">
          <span className="path-viewer__scroll-icon">📜</span>
          <p>Enter two concepts above and press <strong>Go Down the Rabbit Hole</strong></p>
          <p className="path-viewer__sub">The knowledge path will appear here</p>
        </div>
      </div>
    );
  }

  return (
    <div className="path-viewer">
      <div className="path-viewer__header">
        <span className="path-viewer__tag">Rabbit Hole</span>
        <h2 className="path-viewer__title">
          {hole.concept_a} <span>→</span> {hole.concept_b}
        </h2>
        <p className="path-viewer__meta">
          {hole.steps.length} steps &bull; {new Date(hole.created_at).toLocaleDateString()}
        </p>
      </div>

      <div className="path-viewer__steps">
        {hole.steps.map((step, i) => (
          <PathCard
            key={step.step}
            step={step}
            isFirst={i === 0}
            isLast={i === hole.steps.length - 1}
          />
        ))}
      </div>
    </div>
  );
}
