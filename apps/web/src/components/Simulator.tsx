"use client";

import { useQuery } from "@tanstack/react-query";
import { useEffect, useRef } from "react";

import { CharacterSetup } from "@/components/CharacterSetup";
import { EncounterPanel } from "@/components/EncounterPanel";
import { ResultsDashboard } from "@/components/ResultsDashboard";
import { api, type WowClass } from "@/lib/api";
import { loadFallbackClasses } from "@/lib/catalogFallback";
import { useSimulatorStore } from "@/lib/store";

async function loadClasses(): Promise<{ classes: WowClass[]; source: "api" | "fallback"; warning?: string }> {
  try {
    const classes = await api.classes();
    if (!classes.length) {
      throw new Error("API вернул пустой список классов");
    }
    return { classes, source: "api" };
  } catch (err) {
    const message = err instanceof Error ? err.message : "API недоступен";
    const classes = await loadFallbackClasses();
    return {
      classes,
      source: "fallback",
      warning: `Каталог загружен локально (API: ${message}). Симуляция потребует работающий backend.`,
    };
  }
}

export function Simulator() {
  const store = useSimulatorStore();
  const bootedSpec = useRef(false);

  const classesQuery = useQuery({
    queryKey: ["classes"],
    queryFn: loadClasses,
    retry: 1,
  });

  const healthQuery = useQuery({
    queryKey: ["health"],
    queryFn: api.health,
    retry: 1,
  });

  const buildQuery = useQuery({
    queryKey: ["builds-current"],
    queryFn: api.buildsCurrent,
    retry: 1,
  });

  const classes = classesQuery.data?.classes ?? [];

  useEffect(() => {
    if (!classesQuery.data?.classes.length || bootedSpec.current) return;
    const data = classesQuery.data.classes;
    store.setClasses(data);
    if (classesQuery.data.warning) {
      store.setError(classesQuery.data.warning);
    }
    bootedSpec.current = true;
    void (async () => {
      if (store.specId) return;
      const shadow =
        data
          .flatMap((c) => c.specs.map((s) => ({ ...s, classId: c.id, className: c.name })))
          .find((s) => s.key === "priest_shadow" || s.id === 258) ?? data.flatMap((c) => c.specs)[0];
      if (!shadow) return;
      try {
        const full = await api.spec(shadow.id);
        store.selectSpec(full);
      } catch {
        store.selectSpec(shadow);
      }
    })();
  }, [classesQuery.data, store]);

  async function runSimulate() {
    if (!store.specId) return;
    if (store.mode !== "fast_estimate" && store.selectedSpec && !store.selectedSpec.canAccurate) {
      store.setError("Accurate недоступен для этой специализации. Переключитесь на Fast Estimate.");
      return;
    }
    store.setLoading(true);
    store.setError(null);
    store.setCompareResult(null);
    try {
      const job = await api.simulate(store.buildRequest(), true);
      if (job.status !== "succeeded" || !job.result) {
        throw new Error(job.error || `Simulation ${job.status}`);
      }
      store.setResult(job.result);
    } catch (err) {
      store.setError(err instanceof Error ? err.message : "Ошибка симуляции");
      store.setResult(null);
    } finally {
      store.setLoading(false);
    }
  }

  async function runCompare() {
    if (!store.specId || !store.baselineResult) {
      store.setError("Сначала закрепите baseline.");
      return;
    }
    store.setLoading(true);
    store.setError(null);
    try {
      const current = store.buildRequest();
      const baselineReq = {
        ...current,
        rotation: { ...(current.rotation as object), disabledActions: [] },
      };
      const cmp = await api.compare({
        fight: current.fight,
        gear: current.gear,
        buildA: baselineReq,
        buildB: current,
        seed: 417391,
      });
      store.setCompareResult(cmp);
    } catch (err) {
      store.setError(err instanceof Error ? err.message : "Ошибка сравнения");
    } finally {
      store.setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-[1500px] px-4 py-6 md:px-6">
      <header className="mb-6 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div className="fade-in">
          <p className="text-xs uppercase tracking-[0.25em] text-[var(--muted)]">
            World of Warcraft: Midnight
          </p>
          <h1 className="mt-1 font-[family-name:var(--font-display)] text-4xl font-bold text-[var(--accent)] md:text-5xl">
            DPS Lab
          </h1>
          <p className="mt-2 max-w-2xl text-[var(--muted)]">
            Калькулятор DPS для патча 12.1.5: Fast Estimate для интерактива и SimulationCraft для Accurate Monte
            Carlo. Все 13 классов и 40 специализаций в реестре.
          </p>
        </div>
        <div className="panel px-4 py-3 text-sm text-[var(--muted)]">
          <div>
            Patch:{" "}
            <span className="text-[var(--text)]">
              {buildQuery.data?.patch ?? healthQuery.data?.gameVersion ?? "12.1.5"}
            </span>
          </div>
          <div>
            Build:{" "}
            <span className="text-[var(--text)]">
              {buildQuery.data?.clientBuild ?? healthQuery.data?.clientBuild ?? "70448"}
            </span>
          </div>
          <div>
            Hotfix:{" "}
            <span className="text-[var(--text)]">
              {buildQuery.data?.hotfixDate ?? healthQuery.data?.hotfixDate ?? "—"}
            </span>
          </div>
          <div>
            Engine: <span className="text-[var(--text)]">{healthQuery.data?.engine ?? "…"}</span>
          </div>
          <div>
            Классы/спеки:{" "}
            <span className="text-[var(--text)]">
              {classes.length || healthQuery.data?.classCount || "—"}/
              {classes.reduce((n, c) => n + c.specs.length, 0) || healthQuery.data?.specCount || "—"}
            </span>
          </div>
        </div>
      </header>

      {store.demoBanner && (
        <div className="mb-4 rounded-xl border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-amber-100">
          Demo / Mock engine — не используйте как реальный SimC результат.
        </div>
      )}

      {classesQuery.isLoading && (
        <div className="mb-4 rounded-xl border border-[var(--line)] bg-black/20 px-4 py-3 text-[var(--muted)]">
          Загрузка каталога классов…
        </div>
      )}

      {classesQuery.isError && (
        <div className="mb-4 rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-rose-100">
          Не удалось загрузить классы:{" "}
          {classesQuery.error instanceof Error ? classesQuery.error.message : "unknown error"}
        </div>
      )}

      {store.error && (
        <div className="mb-4 rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-rose-100">
          {store.error}
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-[320px_minmax(0,1fr)_360px]">
        <CharacterSetup classes={classes} loading={classesQuery.isLoading} />
        <EncounterPanel />
        <ResultsDashboard onSimulate={runSimulate} onCompare={runCompare} />
      </div>
    </div>
  );
}
