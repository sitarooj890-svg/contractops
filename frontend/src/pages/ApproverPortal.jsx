export default function ApproverPortal() {
  return (
    <main className="page page-wide">
      <h2>Approver Portal</h2>
      <div className="card-grid">
        <section className="card">
          <h3>Pending Approvals</h3>
          <p className="muted">
            Obligations waiting for your confirm, correct or reject decision
            will appear here.
          </p>
        </section>
        <section className="card">
          <h3>Upcoming Deadlines</h3>
          <p className="muted">
            Obligations due soon will appear here.
          </p>
        </section>
      </div>
    </main>
  )
}
