export default function LoadingOverlay() {
  return (
    <div className="loading-overlay">
      <div className="loading-overlay__inner">
        <div className="loading-overlay__spinner">🐇</div>
        <p className="loading-overlay__text">Descending into the rabbit hole…</p>
        <p className="loading-overlay__sub">Fetching Wikipedia context &amp; tracing the path</p>
      </div>
    </div>
  );
}
