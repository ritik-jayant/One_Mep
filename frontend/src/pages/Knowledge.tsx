import { useEffect, useState } from "react";
import { api } from "../api";

type Skill = { id: number; code: string; title: string; occupancy: string; category: string; requirement: string };
type Issue = { id: number; severity: string; issue: string; correction: string | null; occupancy: string };
type Plan = { id: number; name: string; occupancy: string; summary: string };

export default function Knowledge() {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [issues, setIssues] = useState<Issue[]>([]);
  const [plans, setPlans] = useState<Plan[]>([]);

  useEffect(() => {
    void Promise.all([api.nbc(), api.issues(), api.approved()]).then(([s, i, p]) => {
      setSkills(s as Skill[]);
      setIssues(i as Issue[]);
      setPlans(p as Plan[]);
    });
  }, []);

  return (
    <div className="grid two">
      <div className="card">
        <h3>NBC skills</h3>
        <p>Rules the matcher retrieves. Engineers can add more via the API.</p>
        {skills.map((s) => (
          <div className="skill" key={s.id}>
            <strong>
              {s.code} · {s.title}
            </strong>
            <div>
              <small>
                {s.occupancy} / {s.category}
              </small>
            </div>
            <p>{s.requirement}</p>
          </div>
        ))}
      </div>
      <div>
        <div className="card">
          <h3>Design store (past issues)</h3>
          {issues.map((i) => (
            <div className="skill" key={i.id}>
              <span className="badge retry">{i.severity}</span> {i.issue}
              {i.correction && <p>Fix: {i.correction}</p>}
            </div>
          ))}
          {!issues.length && <p>No issues yet. Denials, eval failures and engineer edits land here.</p>}
        </div>
        <div className="card" style={{ marginTop: 16 }}>
          <h3>Approved plan library</h3>
          {plans.map((pl) => (
            <div className="skill" key={pl.id}>
              <strong>{pl.name}</strong>
              <p>
                {pl.occupancy}: {pl.summary}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
