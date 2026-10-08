export default function AnalystPortal() {
  return (
    <main className="page page-wide">
      <h2>Analyst Portal</h2>
      <div className="card-grid">
        <section className="card">
          <h3>Your Contracts</h3>
          <p className="muted">
            Contracts you uploaded will appear here.
          </p>
        </section>
        <section className="card">
          <h3>Draft Obligations</h3>
          <p className="muted">
            Obligations in draft waiting for review will appear here.
          </p>
        </section>
      </div>
    </main>
  )
}
