"use client";

import { create } from "zustand";

import type { ComparisonResult, SimulationResult, Spec, WowClass } from "@/lib/api";

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
  mode: "quick" | "accurate";
  gearPreset: "entry" | "mid" | "high" | "custom";
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
  setMode: (mode: "quick" | "accurate") => void;
  setGearPreset: (preset: "entry" | "mid" | "high" | "custom") => void;
  resetRotation: () => void;
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
  heroTalent: null,
  talentString: "",
  disabledActions: [],
  priority: [],
  rotationMode: "automatic",
  customApl: "",
  rawSimcProfile: "",
  targets: 1,
  duration: 180,
  fightStyle: "Patchwerk",
  mode: "quick",
  gearPreset: "high",
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
  setGearPreset: (preset) => set({ gearPreset: preset }),
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
    return {
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
        latencyMs: 50,
      },
    };
  },
}));
