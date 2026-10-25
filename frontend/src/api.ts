const jsonHeaders = { "Content-Type": "application/json" };

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, init);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return res.json() as Promise<T>;
}

export type Project = {
  id: number;
  name: string;
  occupancy: string;
  status: string;
  drawing_path: string | null;
  dxf_path: string | null;
  generation_attempt: number;
};

export type ProjectDetail = Project & {
  matched_rules: {
    occupancy_detected?: string;
    building_notes?: string;
    rationale?: string;
    skills?: { code: string; title: string; category: string; requirement: string }[];
  } | null;
  design: Record<string, unknown> | null;
  evaluation: { pass?: boolean; score?: number; failures?: string[]; improvements?: string[] } | null;
  events: { id: number; step: string; outcome: string; detail: string | null; created_at: string | null }[];
};

export const api = {
  health: () => req<{ status: string; llm: string }>("/api/health"),
  listProjects: () => req<Project[]>("/api/projects"),
  createProject: (name: string, occupancy: string) =>
    req<Project>("/api/projects", {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify({ name, occupancy }),
    }),
  getProject: (id: number) => req<ProjectDetail>(`/api/projects/${id}`),
  upload: async (id: number, file: File, occupancy?: string) => {
    const body = new FormData();
    body.append("file", file);
    if (occupancy) body.append("occupancy", occupancy);
    return req<Project>(`/api/projects/${id}/upload`, { method: "POST", body });
  },
  confirm: (id: number, approved: boolean, notes: string) =>
    req<Project>(`/api/projects/${id}/confirm-rules`, {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify({ approved, notes }),
    }),
  recheck: (id: number) => req<Project>(`/api/projects/${id}/recheck-nbc`, { method: "POST" }),
  retry: (id: number) => req<Project>(`/api/projects/${id}/retry-generate`, { method: "POST" }),
  validate: (id: number, change_type: "none" | "minor" | "major", notes: string) =>
    req<Project>(`/api/projects/${id}/validate`, {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify({ change_type, notes }),
    }),
  nbc: () => req<unknown[]>("/api/knowledge/nbc"),
  issues: () => req<unknown[]>("/api/knowledge/issues"),
  approved: () => req<unknown[]>("/api/knowledge/approved"),
  dxfUrl: (id: number) => `/api/projects/${id}/dxf`,
};
