"use client";

import { api, readinessLabel, type WowClass } from "@/lib/api";
import { useSimulatorStore } from "@/lib/store";

function readinessBadge(status: string) {
  if (status === "verified") return "bg-emerald-500/20 text-emerald-300";
  if (status === "implemented") return "bg-sky-500/20 text-sky-200";
  if (status === "partial") return "bg-amber-500/20 text-amber-200";
  return "bg-rose-500/20 text-rose-200";
}

export function CharacterSetup({ classes, loading = false }: { classes: WowClass[]; loading?: boolean }) {
  const store = useSimulatorStore();
  const selectedClass = classes.find((c) => c.id === store.classId) ?? null;
  const specs = selectedClass?.specs ?? [];

  async function pickSpec(specId: number) {
    try {
      store.selectSpec(await api.spec(specId));
    } catch {
      const local = classes.flatMap((c) => c.specs).find((s) => s.id === specId);
      if (local) store.selectSpec(local);
      else store.setError("Не удалось загрузить специализацию");
    }
  }

  return (
    <aside className="panel fade-in space-y-4 p-4">
      <h2 className="font-[family-name:var(--font-display)] text-lg text-[var(--accent)]">Персонаж</h2>

      {loading && <p className="text-xs text-[var(--muted)]">Загрузка классов…</p>}
      {!loading && classes.length === 0 && (
        <p className="rounded-md border border-rose-500/40 bg-rose-500/10 px-2 py-2 text-xs text-rose-100">
          Каталог классов пуст. Проверьте, что API запущен и доступен через /api/v1.
        </p>
      )}

      <div>
        <label className="label">Класс ({classes.length})</label>
        <select
          className="select"
          value={store.classId ?? ""}
          disabled={classes.length === 0}
          onChange={async (e) => {
            const id = Number(e.target.value);
            store.selectClass(id);
            const cls = classes.find((c) => c.id === id);
            const first = cls?.specs[0];
            if (first) await pickSpec(first.id);
          }}
        >
          <option value="" disabled>
            {classes.length ? "Выберите класс" : "Нет классов"}
          </option>
          {classes.map((c) => (
            <option key={c.id} value={c.id}>
              {c.nameRu ? `${c.nameRu} / ${c.name}` : c.name}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="label">Специализация ({specs.length})</label>
        <select
          className="select"
          value={store.specId ?? ""}
          disabled={specs.length === 0}
          onChange={async (e) => pickSpec(Number(e.target.value))}
        >
          <option value="" disabled>
            {specs.length ? "Выберите специализацию" : "Сначала выберите класс"}
          </option>
          {specs.map((s) => (
            <option key={s.id} value={s.id}>
              {s.nameRu ? `${s.nameRu} / ${s.name}` : s.name} ({readinessLabel(s.readiness ?? s.simulationSupport)})
            </option>
          ))}
        </select>
        {store.selectedSpec && (
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <span
              className={`inline-flex rounded-md px-2 py-0.5 text-xs ${readinessBadge(store.selectedSpec.readiness ?? store.selectedSpec.simulationSupport)}`}
            >
              {readinessLabel(store.selectedSpec.readiness ?? store.selectedSpec.simulationSupport)}
            </span>
            <span className="text-xs text-[var(--muted)]">{store.selectedSpec.key}</span>
            <span className="text-xs text-[var(--muted)]">{store.selectedSpec.role}</span>
          </div>
        )}
        {store.selectedSpec?.notes && (
          <p className="mt-2 text-xs text-[var(--muted)]">{store.selectedSpec.notes}</p>
        )}
      </div>

      <div>
        <label className="label">Hero Talents</label>
        <select
          className="select"
          value={store.heroTalent ?? ""}
          onChange={(e) => store.setHeroTalent(e.target.value || null)}
        >
          {(store.selectedSpec?.heroTalentTrees ?? []).length === 0 && (
            <option value="">Нет данных дерева</option>
          )}
          {(store.selectedSpec?.heroTalentTrees ?? []).map((h) => (
            <option key={h.id} value={h.simcToken ?? h.id}>
              {h.name}
            </option>
          ))}
        </select>
      </div>

      <TalentEditor />
      <AbilityEditor />
      <GearEditor />
    </aside>
  );
}

function TalentEditor() {
  const store = useSimulatorStore();
  const tree = store.selectedSpec?.talentTree;
  const nodes = [...(tree?.classNodes ?? []), ...(tree?.specNodes ?? []), ...(tree?.apexNodes ?? [])];

  async function importTalents() {
    if (!store.talentString || !store.specId) return;
    try {
      const res = await api.importTalents(store.talentString, store.specId);
      if (!res.ok) throw new Error(res.error || "Import failed");
      store.setError(null);
    } catch (err) {
      store.setError(err instanceof Error ? err.message : "Ошибка импорта талантов");
    }
  }

  return (
    <div>
      <label className="label">Таланты</label>
      {nodes.length > 0 ? (
        <div className="mb-2 grid max-h-40 grid-cols-2 gap-1 overflow-auto">
          {nodes.map((node) => {
            const on = store.selectedNodeIds.includes(node.id);
            return (
              <button
                key={node.id}
                type="button"
                className={`rounded-md border px-2 py-1 text-left text-xs ${on ? "border-[var(--accent)] bg-[var(--accent)]/15" : "border-[var(--line)]"}`}
                onClick={() => store.toggleNode(node.id)}
              >
                {node.nameRu || node.name}
              </button>
            );
          })}
        </div>
      ) : (
        <p className="mb-2 text-xs text-[var(--muted)]">
          Интерактивное дерево узлов пока partial — используйте Hero Talent и строку экспорта Blizzard.
        </p>
      )}
      <textarea
        className="textarea"
        placeholder="Вставьте talent string из игры"
        value={store.talentString}
        onChange={(e) => store.setTalentString(e.target.value)}
      />
      <button type="button" className="btn btn-ghost mt-2 w-full" onClick={importTalents}>
        Проверить импорт
      </button>
    </div>
  );
}

function AbilityEditor() {
  const store = useSimulatorStore();
  const abilities = store.selectedSpec?.abilities ?? [];

  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <label className="label mb-0">Способности</label>
        <button type="button" className="text-xs text-[var(--accent)]" onClick={store.resetRotation}>
          Сброс
        </button>
      </div>
      <div className="max-h-56 space-y-2 overflow-auto pr-1">
        {abilities.length === 0 && (
          <p className="text-xs text-[var(--muted)]">Каталог способностей пуст для этой спеки.</p>
        )}
        {abilities.map((ability) => {
          const disabled = store.disabledActions.includes(ability.simcAction);
          return (
            <label
              key={ability.id}
              className="flex cursor-pointer items-start gap-2 rounded-lg border border-[var(--line)] px-2 py-2 text-sm"
            >
              <input
                type="checkbox"
                className="mt-1"
                checked={!disabled}
                onChange={() => store.toggleAbility(ability.simcAction)}
              />
              <span>
                <span className="block font-semibold">
                  {ability.nameRu || ability.name}
                  {ability.nameRu ? (
                    <span className="ml-1 font-normal text-[var(--muted)]">({ability.name})</span>
                  ) : null}
                </span>
                <span className="text-xs text-[var(--muted)]">
                  {ability.simcAction} · {ability.aoeClass}
                  {ability.optional ? "" : " · обязательная"}
                </span>
              </span>
            </label>
          );
        })}
      </div>

      {store.rotationMode === "custom" && (
        <div className="mt-3 space-y-1">
          <label className="label">Приоритет</label>
          {store.priority.map((action) => (
            <div key={action} className="flex items-center justify-between gap-2 text-xs">
              <span>{action}</span>
              <span className="flex gap-1">
                <button type="button" className="btn btn-ghost !px-2 !py-1" onClick={() => store.movePriority(action, -1)}>
                  ↑
                </button>
                <button type="button" className="btn btn-ghost !px-2 !py-1" onClick={() => store.movePriority(action, 1)}>
                  ↓
                </button>
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function GearEditor() {
  const store = useSimulatorStore();
  return (
    <div className="space-y-2">
      <label className="label">Экипировка / статы</label>
      <select
        className="select"
        value={store.gearPreset}
        onChange={(e) => store.setGearPreset(e.target.value as "entry" | "mid" | "high" | "custom")}
      >
        <option value="high">High (MID1)</option>
        <option value="mid">Mid (alias MID1)</option>
        <option value="entry">Entry (alias MID1)</option>
        <option value="custom">Custom ratings</option>
      </select>
      {store.gearPreset === "custom" && (
        <div className="grid grid-cols-2 gap-2">
          {(
            [
              ["critRating", "Crit"],
              ["hasteRating", "Haste"],
              ["masteryRating", "Mastery"],
              ["versRating", "Vers"],
            ] as const
          ).map(([key, label]) => (
            <div key={key}>
              <label className="label">{label}</label>
              <input
                className="input"
                type="number"
                value={store[key] ?? ""}
                onChange={(e) =>
                  store.setRatings({ [key]: e.target.value === "" ? null : Number(e.target.value) })
                }
              />
            </div>
          ))}
        </div>
      )}
      <textarea
        className="textarea"
        placeholder="Опционально: raw SimC profile"
        value={store.rawSimcProfile}
        onChange={(e) => store.setRawSimcProfile(e.target.value)}
      />
    </div>
  );
}
