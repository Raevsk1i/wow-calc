const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000/api/v1";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body?.detail?.message ?? JSON.stringify(body?.detail ?? body);
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export type SimulationSupport = "supported" | "experimental" | "unsupported";

export interface Ability {
  id: string;
  name: string;
  simcAction: string;
  category: string;
  optional: boolean;
  aoeClass: string;
  cooldown?: number | null;
  description?: string | null;
}

export interface HeroTalentTree {
  id: string;
  name: string;
  simcToken?: string | null;
}

export interface Spec {
  id: number;
  classId: number;
  className: string;
  name: string;
  role: string;
  resourceType: string;
  simulationSupport: SimulationSupport;
  heroTalentTrees: HeroTalentTree[];
  abilities: Ability[];
  notes?: string | null;
  defaultHeroTalent?: string | null;
  presetProfile?: string | null;
}

export interface WowClass {
  id: number;
  name: string;
  color: string;
  specs: Spec[];
}

export interface AbilityBreakdownRow {
  name: string;
  spellId?: number | null;
  damage: number;
  pctTotal: number;
  casts: number;
  avgHit?: number | null;
  dps?: number | null;
}

export interface SimulationResult {
  meanDps: number;
  minDps?: number | null;
  maxDps?: number | null;
  medianDps?: number | null;
  stdDev?: number | null;
  meanStdDev?: number | null;
  totalDamage?: number | null;
  fightLength?: number | null;
  iterations?: number | null;
  targets?: number | null;
  breakdown: AbilityBreakdownRow[];
  gameVersion: string;
  simcVersion: string;
  simcCommit: string;
  dataSnapshotId: string;
  sources: string[];
  engine: string;
  isDemo: boolean;
  warnings: string[];
}

export interface SimulationJob {
  id: string;
  status: "queued" | "running" | "succeeded" | "failed" | "cancelled";
  createdAt: string;
  updatedAt: string;
  result?: SimulationResult | null;
  error?: string | null;
}

export interface ComparisonResult {
  jobAId: string;
  jobBId: string;
  dpsA: number;
  dpsB: number;
  absoluteDiff: number;
  percentDiff: number;
  significant: boolean;
  note: string;
  breakdownDiff: Array<{
    name: string;
    damageA: number;
    damageB: number;
    absoluteDiff: number;
  }>;
}

export const api = {
  health: () => request<{ ok: boolean; engine: string; gameVersion: string }>("/health"),
  classes: () => request<WowClass[]>("/classes"),
  spec: (id: number) => request<Spec>(`/specs/${id}`),
  importTalents: (exportString: string, expectedSpecId?: number) =>
    request<{ ok: boolean; specId?: number; error?: string; warnings: string[] }>("/talents/import", {
      method: "POST",
      body: JSON.stringify({ exportString, expectedSpecId }),
    }),
  simulate: (body: unknown, sync = true) =>
    request<SimulationJob>(`/simulations?sync=${sync}`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  getSimulation: (id: string) => request<SimulationJob>(`/simulations/${id}`),
  compare: (body: unknown) =>
    request<ComparisonResult>("/comparisons", {
      method: "POST",
      body: JSON.stringify(body),
    }),
};

export function formatDps(value: number): string {
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(value);
}
