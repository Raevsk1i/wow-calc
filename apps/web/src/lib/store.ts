"use client";

import { create } from "zustand";

import type { ComparisonResult, SimulationResult, Spec, WowClass } from "@/lib/api";

export type SimMode = "fast_estimate" | "quick" | "accurate";
export type RotationMode =
  | "automatic"
  | "custom"
  | "burst_focus"
  | "sustained"
  | "aoe_optimization";

export interface DraftState {
  classId: number | null;
  specId: number | null;
  specKey: string | null;
  heroTalent: string | null;
  talentString: string;
  selectedNodeIds: number[];
  disabledActions: string[];
  priority: string[];
  rotationMode: RotationMode;
  customApl: string;
  rawSimcProfile: string;
  targets: number;
  duration: number;
  fightStyle: string;
  encounterPreset: string;
  clusterRadiusYards: number;
  mode: SimMode;
  gearPreset: "entry" | "mid" | "high" | "custom";
  critRating: number | null;
  hasteRating: number | null;
  masteryRating: number | null;
  versRating: number | null;
  damageActivityShare: number;
  allyModelEnabled: boolean;
  allyCount: number;
  allyMeanDps: number;
  raid: {
    arcaneIntellect: boolean;
    battleShout: boolean;
    markOfTheWild: boolean;
    skyfury: boolean;
    bloodlust: boolean;
    chaosBrand: boolean;
    mysticTouch: boolean;
  };
  classes: WowClass[];
  selectedSpec: Spec | null;
  result: SimulationResult | null;
  compareResult: ComparisonResult | null;
  baselineResult: SimulationResult | null;
  loading: boolean;
  error: string | null;
  demoBanner: boolean;
  stale: boolean;

  setClasses: (classes: WowClass[]) => void;
  selectClass: (classId: number) => void;
  selectSpec: (spec: Spec) => void;
  setHeroTalent: (token: string | null) => void;
  setTalentString: (value: string) => void;
  toggleNode: (nodeId: number) => void;
  toggleAbility: (simcAction: string) => void;
  setRotationMode: (mode: RotationMode) => void;
  setPriority: (actions: string[]) => void;
  movePriority: (action: string, direction: -1 | 1) => void;
  setCustomApl: (value: string) => void;
  setRawSimcProfile: (value: string) => void;
  setTargets: (n: number) => void;
  setDuration: (n: number) => void;
  setFightStyle: (style: string) => void;
  setEncounterPreset: (preset: string) => void;
  setClusterRadius: (n: number) => void;
  setMode: (mode: SimMode) => void;
  setGearPreset: (preset: "entry" | "mid" | "high" | "custom") => void;
  setRatings: ( partial: Partial<Pick<DraftState, "critRating" | "hasteRating" | "masteryRating" | "versRating">>) => void;
  setDamageActivityShare: (n: number) => void;
  setAllyModel: (partial: Partial<Pick<DraftState, "allyModelEnabled" | "allyCount" | "allyMeanDps">>) => void;
  toggleRaid: (key: keyof DraftState["raid"]) => void;
  resetRotation: () => void;
  invalidate: () => void;
  setLoading: (v: boolean) => void;
  setError: (v: string | null) => void;
  setResult: (r: SimulationResult | null) => void;
  setCompareResult: (r: ComparisonResult | null) => void;
  pinBaseline: () => void;
  buildRequest: () => Record<string, unknown>;
}

export const useSimulatorStore = create<DraftState>((set, get) => ({
  classId: null,
  specId: null,
  specKey: null,
  heroTalent: null,
  talentString: "",
  selectedNodeIds: [],
  disabledActions: [],
  priority: [],
  rotationMode: "automatic",
  customApl: "",
  rawSimcProfile: "",
  targets: 1,
  duration: 300,
  fightStyle: "Patchwerk",
  encounterPreset: "boss_patchwerk",
  clusterRadiusYards: 5,
  mode: "fast_estimate",
  gearPreset: "high",
  critRating: null,
  hasteRating: null,
  masteryRating: null,
  versRating: null,
  damageActivityShare: 1,
  allyModelEnabled: false,
  allyCount: 4,
  allyMeanDps: 50000,
  raid: {
    arcaneIntellect: true,
    battleShout: true,
    markOfTheWild: true,
    skyfury: true,
    bloodlust: true,
    chaosBrand: true,
    mysticTouch: true,
  },
  classes: [],
  selectedSpec: null,
  result: null,
  compareResult: null,
  baselineResult: null,
  loading: false,
  error: null,
  demoBanner: false,
  stale: false,

  setClasses: (classes) => set({ classes }),
  selectClass: (classId) =>
    set({ classId, specId: null, specKey: null, selectedSpec: null, result: null, stale: true }),
  selectSpec: (spec) =>
    set({
      classId: spec.classId,
      specId: spec.id,
      specKey: spec.key,
      selectedSpec: spec,
      heroTalent: spec.defaultHeroTalent ?? spec.heroTalentTrees[0]?.simcToken ?? null,
      disabledActions: [],
      selectedNodeIds: [],
      talentString: "",
      priority: spec.abilities
        .filter((a) => a.category === "active" || a.category === "required")
        .map((a) => a.simcAction),
      damageActivityShare: spec.damageActivityShareDefault ?? 1,
      allyModelEnabled: false,
      result: null,
      compareResult: null,
      error: null,
      stale: false,
    }),
  setHeroTalent: (token) => set({ heroTalent: token, result: null, stale: true }),
  setTalentString: (value) => set({ talentString: value, stale: true, result: null }),
  toggleNode: (nodeId) =>
    set((state) => {
      const setIds = new Set(state.selectedNodeIds);
      if (setIds.has(nodeId)) setIds.delete(nodeId);
      else setIds.add(nodeId);
      return { selectedNodeIds: [...setIds], stale: true, result: null };
    }),
  toggleAbility: (simcAction) =>
    set((state) => {
      const disabled = new Set(state.disabledActions);
      if (disabled.has(simcAction)) disabled.delete(simcAction);
      else disabled.add(simcAction);
      return { disabledActions: [...disabled], stale: true, result: null };
    }),
  setRotationMode: (mode) => set({ rotationMode: mode, stale: true, result: null }),
  setPriority: (actions) => set({ priority: actions, stale: true, result: null }),
  movePriority: (action, direction) =>
    set((state) => {
      const list = [...state.priority];
      const idx = list.indexOf(action);
      if (idx < 0) return state;
      const next = idx + direction;
      if (next < 0 || next >= list.length) return state;
      [list[idx], list[next]] = [list[next], list[idx]];
      return { priority: list, stale: true, result: null };
    }),
  setCustomApl: (value) => set({ customApl: value, stale: true, result: null }),
  setRawSimcProfile: (value) => set({ rawSimcProfile: value, stale: true, result: null }),
  setTargets: (n) => set({ targets: n, stale: true, result: null }),
  setDuration: (n) => set({ duration: n, stale: true, result: null }),
  setFightStyle: (style) => set({ fightStyle: style, stale: true, result: null }),
  setEncounterPreset: (preset) => set({ encounterPreset: preset, stale: true, result: null }),
  setClusterRadius: (n) => set({ clusterRadiusYards: n, stale: true, result: null }),
  setMode: (mode) => set({ mode, stale: true, result: null }),
  setGearPreset: (preset) => set({ gearPreset: preset, stale: true, result: null }),
  setRatings: (partial) => set({ ...partial, gearPreset: "custom", stale: true, result: null }),
  setDamageActivityShare: (n) => set({ damageActivityShare: n, stale: true, result: null }),
  setAllyModel: (partial) => set({ ...partial, stale: true, result: null }),
  toggleRaid: (key) =>
    set((state) => ({
      raid: { ...state.raid, [key]: !state.raid[key] },
      stale: true,
      result: null,
    })),
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
      stale: true,
      result: null,
    });
  },
  invalidate: () => set({ stale: true, result: null }),
  setLoading: (v) => set({ loading: v }),
  setError: (v) => set({ error: v }),
  setResult: (r) => set({ result: r, demoBanner: Boolean(r?.isDemo), stale: false }),
  setCompareResult: (r) => set({ compareResult: r }),
  pinBaseline: () => set({ baselineResult: get().result }),
  buildRequest: () => {
    const s = get();
    const customStats =
      s.gearPreset === "custom"
        ? {
            crit: s.critRating,
            haste: s.hasteRating,
            mastery: s.masteryRating,
            versatility: s.versRating,
          }
        : null;
    return {
      gameVersion: "12.1.5",
      specId: s.specId,
      specKey: s.specKey,
      talents: {
        exportString: s.talentString || null,
        heroTalent: s.heroTalent,
        selectedNodeIds: s.selectedNodeIds,
        useProfileTalents: !s.talentString,
      },
      gear: {
        preset: s.gearPreset,
        customStats,
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
        latencyMs: 50,
        clusterRadiusYards: s.clusterRadiusYards,
        encounterPreset: s.encounterPreset,
        damageActivityShare: s.damageActivityShare,
        raid: s.raid,
        allies: {
          enabled: s.allyModelEnabled,
          allyCount: s.allyCount,
          allyMeanDps: s.allyMeanDps,
          buffUptime: 0.85,
        },
      },
    };
  },
}));
