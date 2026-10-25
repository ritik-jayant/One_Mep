import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api, type ProjectDetail } from "../api";

const STEPS = [
  "uploaded",
  "rules_matched",
  "rules_confirmed",
  "store_checked",
  "design_generated",
  "cad_ready",
  "approved",
];

export default function Workspace() {
  const { id } = useParams();
  const pid = Number(id);
  const [p, setP] = useState<ProjectDetail | null>(null);
  const [notes, setNotes] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function refresh() {
    setP(await api.getProject(pid));
  }

  useEffect(() => {
    void refresh();
  }, [pid]);

  async function run(fn: () => Promise<unknown>) {
    setBusy(true);
    setError("");
    try {
      await fn();
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally {
      setBusy(false);
    }
  }

  if (!p) return <p>Loading…</p>;

  return (
    <div>
      <h1>{p.name}</h1>
      <div className="row">
        <span className="badge">{p.occupancy}</span>
        <span className="badge ok">{p.status}</span>
        <span className="badge">attempt {p.generation_attempt}</span>
      </div>
      {error && <p className="badge retry">{error}</p>}

      <div className="steps">
        {STEPS.map((s) => (
          <span key={s} className={p.status === s || STEPS.indexOf(p.status) >= STEPS.indexOf(s) ? "on" : ""}>
            {s.replaceAll("_", " ")}
          </span>
        ))}
      </div>

      <div className="grid two">
        <div className="card">
          <h3>1. Upload plot</h3>
          <input
            type="file"
            accept="image/*,.pdf"
            disabled={busy}
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) void run(() => api.upload(pid, file, p.occupancy));
            }}
          />
          <p>Saves the drawing, then the agent matches NBC skills.</p>

          <h3 style={{ marginTop: 18 }}>2. Confirm NBC rules</h3>
          {(p.matched_rules?.skills || []).map((s) => (
            <div className="skill" key={s.code}>
              <strong>
                {s.code} — {s.title}
              </strong>
              <div>
                <small>{s.requirement}</small>
              </div>
            </div>
          ))}
          <p>{p.matched_rules?.rationale}</p>
          <label>
            Engineer notes
            <textarea value={notes} onChange={(e) => setNotes(e.target.value)} />
          </label>
          <div className="row" style={{ marginTop: 10 }}>
            <button disabled={busy} onClick={() => void run(() => api.confirm(pid, true, notes))}>
              Confirm rules
            </button>
            <button className="warn" disabled={busy} onClick={() => void run(() => api.confirm(pid, false, notes))}>
              Deny (re-check)
            </button>
            {p.status === "rules_denied" && (
              <button className="llm" disabled={busy} onClick={() => void run(() => api.recheck(pid))}>
                Re-check NBC
              </button>
            )}
          </div>
        </div>

        <div className="card">
          <h3>3–8. Generate, eval, CAD, validate</h3>
          <p>
            After confirm, the agent reads the design store, generates a layout, evaluates against
            approved plans (retries on fail), and writes a DXF.
          </p>
          {p.evaluation && (
            <p>
              Eval:{" "}
              <span className={p.evaluation.pass ? "badge ok" : "badge retry"}>
                {p.evaluation.pass ? "pass" : "failed"}
              </span>{" "}
              score {p.evaluation.score ?? "—"}
            </p>
          )}
          {p.evaluation?.failures?.length ? (
            <ul>
              {p.evaluation.failures.map((f) => (
                <li key={f}>{f}</li>
              ))}
            </ul>
          ) : null}
          {p.status === "eval_failed" && (
            <button className="warn" disabled={busy} onClick={() => void run(() => api.retry(pid))}>
              Retry generate
            </button>
          )}
          {p.dxf_path && (
            <p>
              <a className="badge ok" href={api.dxfUrl(pid)}>
                Download DXF
              </a>
            </p>
          )}
          <div className="row" style={{ marginTop: 12 }}>
            <button disabled={busy || !p.dxf_path} onClick={() => void run(() => api.validate(pid, "none", notes))}>
              Approve to client
            </button>
            <button
              className="ghost"
              disabled={busy || !p.dxf_path}
              onClick={() => void run(() => api.validate(pid, "minor", notes))}
            >
              Minor change
            </button>
            <button
              className="warn"
              disabled={busy || !p.dxf_path}
              onClick={() => void run(() => api.validate(pid, "major", notes))}
            >
              Major change
            </button>
          </div>
          {p.design && <pre>{JSON.stringify(p.design, null, 2)}</pre>}
        </div>
      </div>

      <div className="card" style={{ marginTop: 16 }}>
        <h3>Agent log</h3>
        <ul className="timeline">
          {p.events.map((e) => (
            <li key={e.id}>
              <strong>{e.step}</strong> · {e.outcome}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
