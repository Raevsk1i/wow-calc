"use client";

import { useSimulatorStore, type RotationMode, type SimMode } from "@/lib/store";

const TARGET_PRESETS = [1, 2, 3, 5, 10];

export function EncounterPanel() {
  const store = useSimulatorStore();
  const spec = store.selectedSpec;

  return (
    <section className="panel fade-in space-y-4 p-4">
      <h2 className="font-[family-name:var(--font-display)] text-lg text-[var(--accent)]">
        Бой и ротация
      </h2>

      <div>
        <label className="label">Цели</label>
        <div className="flex flex-wrap gap-2">
          {TARGET_PRESETS.map((n) => (
            <button
              key={n}
              type="button"
              className={`btn ${store.targets === n ? "btn-primary" : "btn-ghost"} !px-3`}
              onClick={() => store.setTargets(n)}
            >
              {n}
            </button>
          ))}
          <input
            className="input max-w-[88px]"
            type="number"
            min={1}
            max={20}
            value={store.targets}
            onChange={(e) => store.setTargets(Number(e.target.value) || 1)}
            aria-label="Custom targets"
          />
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <label className="label">Длительность (с)</label>
          <input
            className="input"
            type="number"
            min={30}
            max={600}
            value={store.duration}
            onChange={(e) => store.setDuration(Number(e.target.value) || 300)}
          />
        </div>
        <div>
          <label className="label">Радиус кластера (ярды)</label>
          <input
            className="input"
            type="number"
            min={1}
            max={40}
            value={store.clusterRadiusYards}
            onChange={(e) => store.setClusterRadius(Number(e.target.value) || 5)}
          />
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <label className="label">Сценарий</label>
          <select
            className="select"
            value={store.encounterPreset}
            onChange={(e) => {
              const preset = e.target.value;
              store.setEncounterPreset(preset);
              if (preset === "boss_patchwerk") {
                store.setFightStyle("Patchwerk");
                store.setTargets(1);
              } else if (preset === "low_cleave") {
                store.setFightStyle("LightMovement");
                store.setTargets(2);
              } else if (preset === "dungeon_pack") {
                store.setFightStyle("DungeonSlice");
                store.setTargets(5);
              } else if (preset === "large_aoe") {
                store.setFightStyle("DungeonSlice");
                store.setTargets(10);
              }
            }}
          >
            <option value="boss_patchwerk">Boss / Patchwerk</option>
            <option value="low_cleave">Low Target Cleave</option>
            <option value="dungeon_pack">Dungeon Pack</option>
            <option value="large_aoe">Large AoE</option>
            <option value="custom">Custom</option>
          </select>
        </div>
        <div>
          <label className="label">Fight style</label>
          <select
            className="select"
            value={store.fightStyle}
            onChange={(e) => store.setFightStyle(e.target.value)}
          >
            <option value="Patchwerk">Patchwerk</option>
            <option value="LightMovement">Light Movement</option>
            <option value="HeavyMovement">Heavy Movement</option>
            <option value="DungeonSlice">Dungeon Slice</option>
            <option value="CastingPatchwerk">Casting Patchwerk</option>
          </select>
        </div>
      </div>

      <div>
        <label className="label">Режим ротации</label>
        <select
          className="select"
          value={store.rotationMode}
          onChange={(e) => store.setRotationMode(e.target.value as RotationMode)}
        >
          <option value="automatic">Auto (рекомендуемая APL)</option>
          <option value="burst_focus">Burst Focus</option>
          <option value="sustained">Sustained DPS</option>
          <option value="aoe_optimization">AoE Optimization</option>
          <option value="custom">Custom</option>
        </select>
      </div>

      {store.rotationMode === "custom" && (
        <div>
          <label className="label">Custom APL</label>
          <textarea
            className="textarea"
            value={store.customApl}
            onChange={(e) => store.setCustomApl(e.target.value)}
            placeholder="actions+=/ability_name"
          />
        </div>
      )}

      <div>
        <label className="label">Режим расчёта</label>
        <select
          className="select"
          value={store.mode}
          onChange={(e) => store.setMode(e.target.value as SimMode)}
        >
          <option value="fast_estimate">Fast Estimate (deterministic)</option>
          <option value="quick">Accurate Quick (SimC, low iter)</option>
          <option value="accurate">Accurate Monte Carlo (SimC)</option>
        </select>
        {store.mode !== "fast_estimate" && !spec?.canAccurate && (
          <p className="mt-2 text-xs text-amber-200">
            Accurate для этой специализации недоступен на текущем pin (нет рабочего MID preset). Используйте Fast
            Estimate.
          </p>
        )}
      </div>

      {spec?.role === "HEALER" && (
        <div>
          <label className="label">Доля активности на урон ({Math.round(store.damageActivityShare * 100)}%)</label>
          <input
            className="w-full"
            type="range"
            min={0.05}
            max={1}
            step={0.05}
            value={store.damageActivityShare}
            onChange={(e) => store.setDamageActivityShare(Number(e.target.value))}
          />
        </div>
      )}

      {spec?.allyModelRequired && (
        <div className="space-y-2 rounded-lg border border-[var(--line)] p-3">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={store.allyModelEnabled}
              onChange={(e) => store.setAllyModel({ allyModelEnabled: e.target.checked })}
            />
            Модель союзников (Augmentation)
          </label>
          {store.allyModelEnabled && (
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="label">Союзники</label>
                <input
                  className="input"
                  type="number"
                  value={store.allyCount}
                  onChange={(e) => store.setAllyModel({ allyCount: Number(e.target.value) || 0 })}
                />
              </div>
              <div>
                <label className="label">Средний DPS союзника</label>
                <input
                  className="input"
                  type="number"
                  value={store.allyMeanDps}
                  onChange={(e) => store.setAllyModel({ allyMeanDps: Number(e.target.value) || 0 })}
                />
              </div>
            </div>
          )}
        </div>
      )}

      <div>
        <label className="label">Рейдовые эффекты</label>
        <div className="grid grid-cols-2 gap-2 text-sm">
          {(
            [
              ["arcaneIntellect", "Arcane Intellect"],
              ["battleShout", "Battle Shout"],
              ["markOfTheWild", "Mark of the Wild"],
              ["skyfury", "Skyfury"],
              ["bloodlust", "Bloodlust"],
              ["chaosBrand", "Chaos Brand"],
              ["mysticTouch", "Mystic Touch"],
            ] as const
          ).map(([key, label]) => (
            <label key={key} className="flex items-center gap-2">
              <input type="checkbox" checked={store.raid[key]} onChange={() => store.toggleRaid(key)} />
              {label}
            </label>
          ))}
        </div>
      </div>
    </section>
  );
}
