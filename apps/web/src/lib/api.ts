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

export type ReadinessStatus = "verified" | "implemented" | "partial" | "unsupported";
export type SimulationSupport = ReadinessStatus;

export interface Ability {
  id: string;
  name: string;
  nameRu?: string | null;
  simcAction: string;
  category: string;
  optional: boolean;
  aoeClass: string;
  cooldown?: number | null;
  description?: string | null;
  dataStatus?: string | null;
  spellId?: number | null;
}

export interface HeroTalentTree {
  id: string;
  name: string;
  simcToken?: string | null;
}

export interface TalentNode {
  id: number;
  name: string;
  nameRu?: string | null;
  maxRanks: number;
  row: number;
  col: number;
  tree: string;
  prerequisites: number[];
  spellId?: number | null;
  description?: string | null;
}

export interface Spec {
  id: number;
  key: string;
  classId: number;
  className: string;
  classNameRu?: string | null;
  name: string;
  nameRu?: string | null;
  role: string;
  attackType?: string;
  primaryStat?: string;
  resourceType: string;
  simulationSupport: ReadinessStatus;
  readiness?: ReadinessStatus;
  canAccurate?: boolean;
  canFastEstimate?: boolean;
  heroTalentTrees: HeroTalentTree[];
  abilities: Ability[];
  talentTree?: {
    classNodes: TalentNode[];
    specNodes: TalentNode[];
    apexNodes?: TalentNode[];
    heroTrees: HeroTalentTree[];
  };
  notes?: string | null;
  defaultHeroTalent?: string | null;
  presetProfile?: string | null;
  allyModelRequired?: boolean;
  damageActivityShareDefault?: number;
  offenseTank?: boolean;
}

export interface WowClass {
  id: number;
  name: string;
  nameRu?: string | null;
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
  personalDps?: number | null;
  effectiveDps?: number | null;
  allyAttributedDps?: number | null;
  minDps?: number | null;
  maxDps?: number | null;
  medianDps?: number | null;
  stdDev?: number | null;
  meanStdDev?: number | null;
  p05Dps?: number | null;
  p95Dps?: number | null;
  confidence95?: number[] | null;
  totalDamage?: number | null;
  fightLength?: number | null;
  iterations?: number | null;
  targets?: number | null;
  breakdown: AbilityBreakdownRow[];
  gameVersion: string;
  simcVersion: string;
  simcCommit: string;
  dataSnapshotId: string;
  clientBuild?: number | null;
  hotfixDate?: string | null;
  sources: string[];
  engine: string;
  isDemo: boolean;
  isApproximation?: boolean;
  assumptions?: string[];
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

export interface RulesetBuild {
  patch?: string;
  clientBuild?: number;
  hotfixDate?: string;
  region?: string;
  dataRevision?: string;
  aplRevision?: string;
  confidence?: string;
  gameVersion?: string;
  dataSnapshotId?: string;
}

export const api = {
  health: () =>
    request<{
      ok: boolean;
      engine: string;
      gameVersion: string;
      clientBuild?: number;
      hotfixDate?: string;
      classCount?: number;
      specCount?: number;
    }>("/health"),
  buildsCurrent: () => request<RulesetBuild>("/builds/current"),
  classes: () => request<WowClass[]>("/classes"),
  specs: () => request<Spec[]>("/specs"),
  spec: (id: number | string) => request<Spec>(`/specs/${id}`),
  raidEffects: () => request<{ buffs: unknown[]; debuffs: unknown[] }>("/raid-effects"),
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
    request<ComparisonResult>("/compare", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  statWeights: (body: unknown) =>
    request<{ baseDps: number; weights: Record<string, number>; isApproximation: boolean }>(
      "/stat-weights",
      { method: "POST", body: JSON.stringify(body) },
    ),
};

export function formatDps(value: number): string {
  return new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 0 }).format(value);
}

export function readinessLabel(status: string): string {
  switch (status) {
    case "verified":
      return "проверено";
    case "implemented":
      return "реализовано";
    case "partial":
      return "частично";
    case "unsupported":
      return "нет Accurate";
    default:
      return status;
  }
}
