import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type Project } from "../api";

const OCC = ["residential", "mercantile", "assembly", "industrial", "institutional"];

export default function Dashboard() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [name, setName] = useState("Plot A fire layout");
  const [occupancy, setOccupancy] = useState("residential");
  const [health, setHealth] = useState("");
  const [error, setError] = useState("");

  async function load() {
    try {
      const [list, h] = await Promise.all([api.listProjects(), api.health()]);
      setProjects(list);
      setHealth(h.llm);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Backend not running");
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    await api.createProject(name, occupancy);
    await load();
  }

  return (
    <div>
      <h1>Engineer workspace</h1>
      <p>
        Upload a client plot, match NBC skills, generate a fire-fighting design, export DXF, and
        teach the agent from every correction. LLM mode: <span className="badge llm">{health || "…"}</span>
      </p>
      {error && <p className="badge retry">{error}</p>}

      <form className="card" onSubmit={onCreate} style={{ margin: "18px 0" }}>
        <h3>New project</h3>
        <div className="row">
          <label>
            Name
            <input value={name} onChange={(e) => setName(e.target.value)} required />
          </label>
          <label>
            Occupancy
            <select value={occupancy} onChange={(e) => setOccupancy(e.target.value)}>
              {OCC.map((o) => (
                <option key={o}>{o}</option>
              ))}
            </select>
          </label>
          <button type="submit">Create</button>
        </div>
      </form>

      <div className="grid cards">
        {projects.map((p) => (
          <Link key={p.id} className="card" to={`/projects/${p.id}`}>
            <h2>{p.name}</h2>
            <div className="row">
              <span className="badge">{p.occupancy}</span>
              <span className="badge ok">{p.status}</span>
            </div>
          </Link>
        ))}
        {!projects.length && <div className="card">No projects yet. Create one and upload a plot diagram.</div>}
      </div>
    </div>
  );
}
