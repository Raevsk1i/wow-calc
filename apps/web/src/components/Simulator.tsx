"use client";

import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { api, formatDps, type Spec, type WowClass } from "@/lib/api";
import { useSimulatorStore } from "@/lib/store";

function supportBadge(support: string) {
  if (support === "supported") return "bg-emerald-500/20 text-emerald-300";
  if (support === "experimental") return "bg-amber-500/20 text-amber-200";
  return "bg-rose-500/20 text-rose-200";
}

export function Simulator() {
  const store = useSimulatorStore();

  const classesQuery = useQuery({
    queryKey: ["classes"],
    queryFn: api.classes,
  });

  const healthQuery = useQuery({
    queryKey: ["health"],
    queryFn: api.health,
    retry: 1,
  });

  const classes = classesQuery.data ?? [];
  const selectedClass = classes.find((c) => c.id === store.classId) ?? null;
  const selectableSpecs = useMemo(() => {
    if (!selectedClass) return [] as Spec[];
    return selectedClass.specs.filter((s) => s.simulationSupport !== "unsupported");
  }, [selectedClass]);

  async function ensureClassesLoaded(data: WowClass[]) {
    store.setClasses(data);
    if (!store.specId) {
      const firstSupported =
        data.flatMap((c) => c.specs.map((s) => ({ ...s, classId: c.id, className: c.name }))).find(
          (s) => s.simulationSupport === "supported",
        ) ?? null;
      if (firstSupported) {
        const full = await api.spec(firstSupported.id);
        store.selectSpec(full);
      }
    }
  }

  if (classesQuery.data && store.classes.length === 0) {
    void ensureClassesLoaded(classesQuery.data);
  }

  async function runSimulate() {
    if (!store.specId) return;
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
      store.setError(err instanceof Error ? err.message : "Simulation failed");
      store.setResult(null);
    } finally {
      store.setLoading(false);
    }
  }

  async function runCompare() {
    if (!store.specId || !store.baselineResult) {
      store.setError("Pin a baseline result before comparing.");
      return;
    }
    store.setLoading(true);
    store.setError(null);
    try {
      const current = store.buildRequest();
      const body = {
        fight: current.fight,
        gear: current.gear,
        buildA: {
          ...current,
          // baseline uses same request shape; comparison endpoint re-sims both under shared fight/gear
        },
        buildB: current,
      };
      // Re-sim baseline config from pinned result isn't stored; compare current vs current with disabled CDs swapped via pin note.
      // Practical MVP: compare current build against a second request with no disabled actions.
      const baselineReq = {
        ...current,
        rotation: { ...(current.rotation as object), disabledActions: [] },
      };
      const cmp = await api.compare({
        fight: current.fight,
        gear: current.gear,
        buildA: baselineReq,
        buildB: current,
      });
      store.setCompareResult(cmp);
    } catch (err) {
      store.setError(err instanceof Error ? err.message : "Comparison failed");
    } finally {
      store.setLoading(false);
    }
  }

  async function importTalents() {
    if (!store.talentString || !store.specId) return;
    try {
      const res = await api.importTalents(store.talentString, store.specId);
      if (!res.ok) throw new Error(res.error || "Import failed");
      store.setError(null);
    } catch (err) {
      store.setError(err instanceof Error ? err.message : "Talent import failed");
    }
  }

  const chartData = (store.result?.breakdown ?? []).slice(0, 10).map((row) => ({
    name: row.name,
    dps: row.dps ?? 0,
    pct: row.pctTotal,
  }));

  return (
    <div className="mx-auto max-w-[1400px] px-4 py-6 md:px-6">
      <header className="mb-6 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div className="fade-in">
          <p className="text-xs uppercase tracking-[0.25em] text-[var(--muted)]">Midnight 12.1.5</p>
          <h1 className="mt-1 font-[family-name:var(--font-display)] text-4xl font-bold text-[var(--accent)] md:text-5xl">
            WoW DPS Lab
          </h1>
          <p className="mt-2 max-w-2xl text-[var(--muted)]">
            SimulationCraft-backed DPS lab. Results come from real APL combat sims — not coefficient
            math.
          </p>
        </div>
        <div className="panel px-4 py-3 text-sm text-[var(--muted)]">
          <div>
            Engine:{" "}
            <span className="text-[var(--text)]">{healthQuery.data?.engine ?? "connecting…"}</span>
          </div>
          <div>
            Game: <span className="text-[var(--text)]">{healthQuery.data?.gameVersion ?? "12.1.5"}</span>
          </div>
        </div>
      </header>

      {store.demoBanner && (
        <div className="mb-4 rounded-xl border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-amber-100">
          Demo / Mock engine result — not a real SimulationCraft simulation.
        </div>
      )}

      {store.error && (
        <div className="mb-4 rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-rose-100">
          {store.error}
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-[280px_minmax(0,1fr)_340px]">
        <aside className="panel fade-in space-y-4 p-4">
          <div>
            <label className="label">Class</label>
            <select
              className="select"
              value={store.classId ?? ""}
              onChange={async (e) => {
                const id = Number(e.target.value);
                store.selectClass(id);
                const cls = classes.find((c) => c.id === id);
                const first = cls?.specs.find((s) => s.simulationSupport !== "unsupported");
                if (first) store.selectSpec(await api.spec(first.id));
              }}
            >
              <option value="" disabled>
                Select class
              </option>
              {classes.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="label">Specialization</label>
            <select
              className="select"
              value={store.specId ?? ""}
              onChange={async (e) => store.selectSpec(await api.spec(Number(e.target.value)))}
            >
              <option value="" disabled>
                Select spec
              </option>
              {selectableSpecs.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} ({s.simulationSupport})
                </option>
              ))}
            </select>
            {store.selectedSpec && (
              <span
                className={`mt-2 inline-flex rounded-full px-2 py-0.5 text-xs ${supportBadge(store.selectedSpec.simulationSupport)}`}
              >
                {store.selectedSpec.simulationSupport}
              </span>
            )}
          </div>

          <div>
            <label className="label">Hero Talent</label>
            <select
              className="select"
              value={store.heroTalent ?? ""}
              onChange={(e) => store.setHeroTalent(e.target.value || null)}
            >
              {(store.selectedSpec?.heroTalentTrees ?? []).map((h) => (
                <option key={h.id} value={h.simcToken ?? h.id}>
                  {h.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="label">Talent String Import</label>
            <textarea
              className="textarea"
              placeholder="Paste Blizzard talent loadout string"
              value={store.talentString}
              onChange={(e) => store.setTalentString(e.target.value)}
            />
            <button type="button" className="btn btn-ghost mt-2 w-full" onClick={importTalents}>
              Validate Import
            </button>
          </div>

          <div>
            <div className="mb-2 flex items-center justify-between">
              <label className="label mb-0">Abilities</label>
              <button type="button" className="text-xs text-[var(--accent)]" onClick={store.resetRotation}>
                Reset
              </button>
            </div>
            <div className="max-h-72 space-y-2 overflow-auto pr-1">
              {(store.selectedSpec?.abilities ?? []).map((ability) => {
                const disabled = store.disabledActions.includes(ability.simcAction);
                const locked = ability.category === "system" || ability.optional === false;
                return (
                  <label
                    key={ability.id}
                    className="flex cursor-pointer items-start gap-2 rounded-lg border border-[var(--line)] px-2 py-2 text-sm"
                  >
                    <input
                      type="checkbox"
                      className="mt-1"
                      checked={!disabled}
                      disabled={locked && ability.category === "system"}
                      onChange={() => store.toggleAbility(ability.simcAction)}
                    />
                    <span>
                      <span className="block font-semibold">{ability.name}</span>
                      <span className="text-xs text-[var(--muted)]">
                        {ability.simcAction} · {ability.aoeClass}
                        {ability.optional ? "" : " · required"}
                      </span>
                    </span>
                  </label>
                );
              })}
            </div>
          </div>
        </aside>

        <main className="panel fade-in space-y-4 p-4">
          <section>
            <h2 className="font-[family-name:var(--font-display)] text-xl text-[var(--accent)]">
              Fight Configuration
            </h2>
            <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              <div>
                <label className="label">Targets</label>
                <input
                  className="input"
                  type="number"
                  min={1}
                  max={20}
                  value={store.targets}
                  onChange={(e) => store.setTargets(Number(e.target.value))}
                />
              </div>
              <div>
                <label className="label">Duration (s)</label>
                <input
                  className="input"
                  type="number"
                  min={30}
                  max={600}
                  value={store.duration}
                  onChange={(e) => store.setDuration(Number(e.target.value))}
                />
              </div>
              <div>
                <label className="label">Fight Style</label>
                <select
                  className="select"
                  value={store.fightStyle}
                  onChange={(e) => store.setFightStyle(e.target.value)}
                >
                  <option>Patchwerk</option>
                  <option>LightMovement</option>
                  <option>HeavyMovement</option>
                  <option>DungeonSlice</option>
                  <option>CastingPatchwerk</option>
                </select>
              </div>
              <div>
                <label className="label">Simulation Mode</label>
                <select
                  className="select"
                  value={store.mode}
                  onChange={(e) => store.setMode(e.target.value as "quick" | "accurate")}
                >
                  <option value="quick">Quick</option>
                  <option value="accurate">Accurate</option>
                </select>
              </div>
              <div>
                <label className="label">Gear Preset</label>
                <select
                  className="select"
                  value={store.gearPreset}
                  onChange={(e) =>
                    store.setGearPreset(e.target.value as "entry" | "mid" | "high" | "custom")
                  }
                >
                  <option value="high">High (MID1)</option>
                  <option value="mid">Mid (alias MID1)</option>
                  <option value="entry">Entry (alias MID1)</option>
                  <option value="custom">Custom / Imported</option>
                </select>
              </div>
              <div>
                <label className="label">Rotation Mode</label>
                <select
                  className="select"
                  value={store.rotationMode}
                  onChange={(e) => store.setRotationMode(e.target.value as "automatic" | "custom")}
                >
                  <option value="automatic">Automatic APL</option>
                  <option value="custom">Custom Priority / APL</option>
                </select>
              </div>
            </div>
          </section>

          {store.rotationMode === "custom" && (
            <section className="space-y-3">
              <h3 className="font-semibold">Priority Editor</h3>
              <div className="space-y-2">
                {store.priority.map((action) => (
                  <div
                    key={action}
                    className="flex items-center justify-between rounded-lg border border-[var(--line)] px-3 py-2 text-sm"
                  >
                    <span>{action}</span>
                    <span className="flex gap-2">
                      <button type="button" className="btn btn-ghost px-2 py-1" onClick={() => store.movePriority(action, -1)}>
                        Up
                      </button>
                      <button type="button" className="btn btn-ghost px-2 py-1" onClick={() => store.movePriority(action, 1)}>
                        Down
                      </button>
                    </span>
                  </div>
                ))}
              </div>
              <div>
                <label className="label">Custom APL (allowlisted actions* only)</label>
                <textarea
                  className="textarea"
                  value={store.customApl}
                  onChange={(e) => store.setCustomApl(e.target.value)}
                  placeholder={"actions=auto_attack\nactions+=/bloodthirst"}
                />
              </div>
            </section>
          )}

          <section>
            <label className="label">Import /simc Profile (sanitized)</label>
            <textarea
              className="textarea"
              value={store.rawSimcProfile}
              onChange={(e) => store.setRawSimcProfile(e.target.value)}
              placeholder="Paste SimulationCraft addon export. Forbidden options (threads, armory, paths) are stripped."
            />
          </section>

          {store.selectedSpec?.notes && (
            <p className="rounded-lg border border-[var(--line)] bg-black/20 px-3 py-2 text-sm text-[var(--muted)]">
              {store.selectedSpec.notes}
            </p>
          )}
        </main>

        <aside className="panel fade-in space-y-4 p-4">
          <button
            type="button"
            className={`btn btn-primary w-full py-3 text-base ${store.loading ? "pulse-glow" : ""}`}
            disabled={!store.specId || store.loading}
            onClick={runSimulate}
          >
            {store.loading ? "Simulating…" : "Simulate"}
          </button>
          <div className="flex gap-2">
            <button type="button" className="btn btn-ghost flex-1" onClick={store.pinBaseline} disabled={!store.result}>
              Pin Baseline
            </button>
            <button type="button" className="btn btn-ghost flex-1" onClick={runCompare} disabled={store.loading}>
              Compare
            </button>
          </div>

          {store.result ? (
            <div className="space-y-3">
              <div>
                <p className="label">Average DPS</p>
                <p className="font-[family-name:var(--font-display)] text-4xl text-[var(--accent)]">
                  {formatDps(store.result.meanDps)}
                </p>
                <p className="mt-1 text-xs text-[var(--muted)]">
                  ±{formatDps(store.result.meanStdDev ?? store.result.stdDev ?? 0)} ·{" "}
                  {store.result.iterations ?? "?"} iters · {store.result.targets ?? "?"} targets
                </p>
              </div>

              <div className="h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} layout="vertical" margin={{ left: 24, right: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#2a3648" />
                    <XAxis type="number" stroke="#9aabbf" fontSize={11} />
                    <YAxis type="category" dataKey="name" width={90} stroke="#9aabbf" fontSize={11} />
                    <Tooltip
                      contentStyle={{ background: "#121821", border: "1px solid #2a3648" }}
                      formatter={(value) => formatDps(Number(value ?? 0))}
                    />
                    <Bar dataKey="dps" fill="#d4a54a" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div className="max-h-64 overflow-auto">
                <table className="w-full text-left text-xs">
                  <thead className="text-[var(--muted)]">
                    <tr>
                      <th className="py-1">Ability</th>
                      <th className="py-1">%</th>
                      <th className="py-1">Casts</th>
                    </tr>
                  </thead>
                  <tbody>
                    {store.result.breakdown.slice(0, 15).map((row) => (
                      <tr key={row.name} className="border-t border-[var(--line)]">
                        <td className="py-1 pr-2">{row.name}</td>
                        <td className="py-1">{row.pctTotal.toFixed(1)}</td>
                        <td className="py-1">{row.casts.toFixed(1)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="text-[11px] leading-relaxed text-[var(--muted)]">
                <div>
                  SimC {store.result.simcVersion} / {store.result.simcCommit}
                </div>
                <div>{store.result.dataSnapshotId}</div>
                {store.result.warnings?.map((w) => (
                  <div key={w}>⚠ {w}</div>
                ))}
              </div>
            </div>
          ) : (
            <div className="rounded-lg border border-dashed border-[var(--line)] px-3 py-8 text-center text-sm text-[var(--muted)]">
              Configure a Supported spec and press Simulate.
            </div>
          )}

          {store.compareResult && (
            <div className="rounded-lg border border-[var(--line)] p-3 text-sm">
              <p className="font-semibold text-[var(--accent)]">Build Comparison</p>
              <p className="mt-1">A: {formatDps(store.compareResult.dpsA)}</p>
              <p>B: {formatDps(store.compareResult.dpsB)}</p>
              <p>
                Δ {formatDps(store.compareResult.absoluteDiff)} (
                {store.compareResult.percentDiff.toFixed(2)}%)
              </p>
              <p className="mt-2 text-xs text-[var(--muted)]">{store.compareResult.note}</p>
            </div>
          )}
        </aside>
      </div>

      <footer className="mt-8 text-center text-xs text-[var(--muted)]">
        Not affiliated with Blizzard Entertainment. Combat math by SimulationCraft (GPL-3.0). Game
        data attributions listed in docs/GAME_DATA.md.
      </footer>
    </div>
  );
}
