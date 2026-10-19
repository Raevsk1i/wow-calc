"use client";

import { create } from "zustand";

import type { ComparisonResult, SimulationResult, Spec, WowClass } from "@/lib/api";

export interface PartyMemberDraft {
  specCanonicalId: string;
  baselineDps: number;
}

export interface DraftState {
  classId: number | null;
  specId: number | null;
  heroTalent: string | null;
  talentString: string;
  disabledActions: string[];
  priority: string[];
  rotationMode: "automatic" | "custom";
  customApl: string;
  rawSimcProfile: string;
  targets: number;
  duration: number;
  fightStyle: string;
  mode: "preview" | "monte_carlo";
  iterations: number | null;
  seed: number | null;
  clusterRadiusYards: number;
  gearPreset: "entry" | "mid" | "high" | "custom";
  raid: {
    arcaneIntellect: boolean;
    battleShout: boolean;
    markOfTheWild: boolean;
    skyfury: boolean;
    chaosBrand: boolean;
    mysticTouch: boolean;
    bloodlustEnabled: boolean;
    bloodlustAtMs: number;
  };
  tankIncomingEnabled: boolean;
  tankAps: number;
  healerDamageActivity: number;
  healerHealingActivity: number;
  partyEnabled: boolean;
  partyMembers: PartyMemberDraft[];
  classes: WowClass[];
  selectedSpec: Spec | null;
  result: SimulationResult | null;
  compareResult: ComparisonResult | null;
  baselineResult: SimulationResult | null;
  loading: boolean;
  error: string | null;
  demoBanner: boolean;

  setClasses: (classes: WowClass[]) => void;
  selectClass: (classId: number) => void;
  selectSpec: (spec: Spec) => void;
  setHeroTalent: (token: string | null) => void;
  setTalentString: (value: string) => void;
  toggleAbility: (simcAction: string) => void;
  setRotationMode: (mode: "automatic" | "custom") => void;
  setPriority: (actions: string[]) => void;
  movePriority: (action: string, direction: -1 | 1) => void;
  setCustomApl: (value: string) => void;
  setRawSimcProfile: (value: string) => void;
  setTargets: (n: number) => void;
  setDuration: (n: number) => void;
  setFightStyle: (style: string) => void;
  setMode: (mode: "preview" | "monte_carlo") => void;
  setIterations: (n: number | null) => void;
  setSeed: (n: number | null) => void;
  setClusterRadiusYards: (n: number) => void;
  setGearPreset: (preset: "entry" | "mid" | "high" | "custom") => void;
  setRaidFlag: (key: keyof DraftState["raid"], value: boolean | number) => void;
  setTankIncomingEnabled: (v: boolean) => void;
  setTankAps: (v: number) => void;
  setHealerDamageActivity: (v: number) => void;
  setHealerHealingActivity: (v: number) => void;
  setPartyEnabled: (v: boolean) => void;
  setPartyMembers: (members: PartyMemberDraft[]) => void;
  resetRotation: () => void;
  setLoading: (v: boolean) => void;
  setError: (v: string | null) => void;
  setResult: (r: SimulationResult | null) => void;
  setCompareResult: (r: ComparisonResult | null) => void;
  pinBaseline: () => void;
  buildRequest: () => Record<string, unknown>;
}

const defaultRaid = {
  arcaneIntellect: true,
  battleShout: true,
  markOfTheWild: true,
  skyfury: true,
  chaosBrand: true,
  mysticTouch: true,
  bloodlustEnabled: true,
  bloodlustAtMs: 0,
};

const defaultParty: PartyMemberDraft[] = [
  { specCanonicalId: "mage_fire", baselineDps: 180000 },
  { specCanonicalId: "warrior_fury", baselineDps: 175000 },
  { specCanonicalId: "hunter_marksmanship", baselineDps: 170000 },
  { specCanonicalId: "warlock_destruction", baselineDps: 165000 },
];

export const useSimulatorStore = create<DraftState>((set, get) => ({
  classId: null,
  specId: null,
  heroTalent: null,
  talentString: "",
  disabledActions: [],
  priority: [],
  rotationMode: "automatic",
  customApl: "",
  rawSimcProfile: "",
  targets: 1,
  duration: 300,
  fightStyle: "Patchwerk",
  mode: "preview",
  iterations: null,
  seed: null,
  clusterRadiusYards: 5,
  gearPreset: "high",
  raid: { ...defaultRaid },
  tankIncomingEnabled: true,
  tankAps: 1.2,
  healerDamageActivity: 1.0,
  healerHealingActivity: 0.0,
  partyEnabled: false,
  partyMembers: defaultParty,
  classes: [],
  selectedSpec: null,
  result: null,
  compareResult: null,
  baselineResult: null,
  loading: false,
  error: null,
  demoBanner: false,

  setClasses: (classes) => set({ classes }),
  selectClass: (classId) => set({ classId, specId: null, selectedSpec: null, result: null }),
  selectSpec: (spec) =>
    set({
      classId: spec.classId,
      specId: spec.id,
      selectedSpec: spec,
      heroTalent: spec.defaultHeroTalent ?? spec.heroTalentTrees[0]?.simcToken ?? null,
      disabledActions: [],
      priority: spec.abilities
        .filter((a) => a.category === "active" || a.category === "required")
        .map((a) => a.simcAction),
      result: null,
      compareResult: null,
      error: null,
    }),
  setHeroTalent: (token) => set({ heroTalent: token }),
  setTalentString: (value) => set({ talentString: value }),
  toggleAbility: (simcAction) =>
    set((state) => {
      const disabled = new Set(state.disabledActions);
      if (disabled.has(simcAction)) disabled.delete(simcAction);
      else disabled.add(simcAction);
      return { disabledActions: [...disabled] };
    }),
  setRotationMode: (mode) => set({ rotationMode: mode }),
  setPriority: (actions) => set({ priority: actions }),
  movePriority: (action, direction) =>
    set((state) => {
      const list = [...state.priority];
      const idx = list.indexOf(action);
      if (idx < 0) return state;
      const next = idx + direction;
      if (next < 0 || next >= list.length) return state;
      [list[idx], list[next]] = [list[next], list[idx]];
      return { priority: list };
    }),
  setCustomApl: (value) => set({ customApl: value }),
  setRawSimcProfile: (value) => set({ rawSimcProfile: value }),
  setTargets: (n) => set({ targets: n }),
  setDuration: (n) => set({ duration: n }),
  setFightStyle: (style) => set({ fightStyle: style }),
  setMode: (mode) => set({ mode }),
  setIterations: (n) => set({ iterations: n }),
  setSeed: (n) => set({ seed: n }),
  setClusterRadiusYards: (n) => set({ clusterRadiusYards: n }),
  setGearPreset: (preset) => set({ gearPreset: preset }),
  setRaidFlag: (key, value) => set((state) => ({ raid: { ...state.raid, [key]: value } })),
  setTankIncomingEnabled: (v) => set({ tankIncomingEnabled: v }),
  setTankAps: (v) => set({ tankAps: v }),
  setHealerDamageActivity: (v) => set({ healerDamageActivity: v }),
  setHealerHealingActivity: (v) => set({ healerHealingActivity: v }),
  setPartyEnabled: (v) => set({ partyEnabled: v }),
  setPartyMembers: (members) => set({ partyMembers: members }),
  resetRotation: () => {
    const spec = get().selectedSpec;
    if (!spec) return;
    set({
      disabledActions: [],
      rotationMode: "automatic",
      customApl: "",
      priority: spec.abilities
        .filter((a) => a.category === "active" || a.category === "required")
        .map((a) => a.simcAction),
    });
  },
  setLoading: (v) => set({ loading: v }),
  setError: (v) => set({ error: v }),
  setResult: (r) => set({ result: r, demoBanner: Boolean(r?.isDemo) }),
  setCompareResult: (r) => set({ compareResult: r }),
  pinBaseline: () => set({ baselineResult: get().result }),
  buildRequest: () => {
    const s = get();
    const role = s.selectedSpec?.role;
    const body: Record<string, unknown> = {
      gameVersion: "12.1.5",
      specId: s.specId,
      talents: {
        exportString: s.talentString || null,
        heroTalent: s.heroTalent,
        useProfileTalents: !s.talentString,
      },
      gear: {
        preset: s.gearPreset,
        rawSimcProfile: s.rawSimcProfile || null,
      },
      rotation: {
        mode: s.rotationMode,
        disabledActions: s.disabledActions,
        priority: s.rotationMode === "custom" ? s.priority : [],
        customApl: s.customApl || null,
      },
      fight: {
        targets: s.targets,
        duration: s.duration,
        fightStyle: s.fightStyle,
        mode: s.mode,
        iterations: s.iterations,
        latencyMs: 50,
        clusterRadiusYards: s.clusterRadiusYards,
      },
      raid: {
        arcaneIntellect: s.raid.arcaneIntellect,
        battleShout: s.raid.battleShout,
        markOfTheWild: s.raid.markOfTheWild,
        skyfury: s.raid.skyfury,
        chaosBrand: s.raid.chaosBrand,
        mysticTouch: s.raid.mysticTouch,
        bloodlust: { enabled: s.raid.bloodlustEnabled, atMs: s.raid.bloodlustAtMs },
      },
      seed: s.seed,
    };
    if (role === "TANK") {
      body.incomingDamageModel = {
        enabled: s.tankIncomingEnabled,
        attacksPerSecond: s.tankAps,
        physicalFraction: 0.75,
        magicFraction: 0.25,
      };
    }
    if (role === "HEALER") {
      body.healerDamageProfile = {
        damageActivity: s.healerDamageActivity,
        healingActivity: s.healerHealingActivity,
      };
    }
    if (role === "SUPPORT") {
      body.party = {
        enabled: s.partyEnabled,
        members: s.partyEnabled ? s.partyMembers : [],
      };
    }
    return body;
  },
}));
