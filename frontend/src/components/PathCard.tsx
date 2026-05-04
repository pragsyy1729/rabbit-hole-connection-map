import type { PathStep } from '../types';

interface Props {
  step: PathStep;
  isFirst: boolean;
  isLast: boolean;
}

export default function PathCard({ step, isFirst, isLast }: Props) {
  return (
    <div className={`path-card ${isFirst ? 'path-card--origin' : ''} ${isLast ? 'path-card--destination' : ''}`}>
      <div className="path-card__label">
        {isFirst ? 'Origin' : isLast ? 'Destination' : `Step ${step.step}`}
      </div>

      <div className="path-card__body">
        <h3 className="path-card__concept">{step.concept}</h3>
        <p className="path-card__extract">{step.wikipedia_extract}</p>
        {step.wikipedia_url && (
          <a
            className="path-card__wiki-link"
            href={step.wikipedia_url}
            target="_blank"
            rel="noreferrer"
          >
            View on Wikipedia ↗
          </a>
        )}
      </div>

      {step.connection_to_next && (
        <div className="path-card__connector">
          <span>↳ connects via: </span>
          <em>{step.connection_to_next}</em>
        </div>
      )}
    </div>
  );
}
