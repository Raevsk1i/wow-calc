"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { formatDps } from "@/lib/api";
import { useSimulatorStore } from "@/lib/store";

export function ResultsDashboard({
  onSimulate,
  onCompare,
}: {
  onSimulate: () => void;
  onCompare: () => void;
}) {
  const store = useSimulatorStore();
  const result = store.result;
  const chartData = (result?.breakdown ?? []).slice(0, 10).map((row) => ({
    name: row.name,
    dps: row.dps ?? 0,
    pct: row.pctTotal,
  }));

  return (
    <aside className="panel fade-in space-y-4 p-4">
      <h2 className="font-[family-name:var(--font-display)] text-lg text-[var(--accent)]">Результаты</h2>

      <div className="flex flex-col gap-2">
        <button
          type="button"
          className={`btn btn-primary w-full ${store.loading ? "pulse-glow" : ""}`}
          disabled={!store.specId || store.loading}
          onClick={onSimulate}
        >
          {store.loading ? "Расчёт…" : "Рассчитать DPS"}
        </button>
        <div className="flex gap-2">
          <button type="button" className="btn btn-ghost flex-1" disabled={!result} onClick={store.pinBaseline}>
            Закрепить baseline
          </button>
          <button
            type="button"
            className="btn btn-ghost flex-1"
            disabled={!store.baselineResult || store.loading}
            onClick={onCompare}
          >
            Сравнить
          </button>
        </div>
      </div>

      {store.stale && result && (
        <p className="text-xs text-amber-200">Параметры изменились — результат устарел.</p>
      )}

      {!result && (
        <p className="text-sm text-[var(--muted)]">
          Выберите специализацию и запустите Fast Estimate или Accurate симуляцию.
        </p>
      )}

      {result && (
        <div className="space-y-3">
          <div className="rounded-xl border border-[var(--line)] bg-black/20 p-3">
            <div className="text-xs uppercase tracking-wide text-[var(--muted)]">
              {result.isApproximation ? "Оценка (approximation)" : "Mean DPS"}
            </div>
            <div className="font-[family-name:var(--font-display)] text-3xl text-[var(--accent)]">
              {formatDps(result.meanDps)}
            </div>
            {result.personalDps != null && (
              <div className="mt-1 text-sm text-[var(--muted)]">
                Personal: {formatDps(result.personalDps)}
                {result.effectiveDps != null ? ` · Effective: ${formatDps(result.effectiveDps)}` : ""}
                {result.allyAttributedDps ? ` · Ally: ${formatDps(result.allyAttributedDps)}` : ""}
              </div>
            )}
            <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-[var(--muted)]">
              {result.medianDps != null && <div>Median: {formatDps(result.medianDps)}</div>}
              {result.stdDev != null && <div>StdDev: {formatDps(result.stdDev)}</div>}
              {result.p05Dps != null && <div>P05: {formatDps(result.p05Dps)}</div>}
              {result.p95Dps != null && <div>P95: {formatDps(result.p95Dps)}</div>}
              {result.totalDamage != null && <div>Урон: {formatDps(result.totalDamage)}</div>}
              {result.targets != null && <div>Цели: {result.targets}</div>}
            </div>
          </div>

          {chartData.length > 0 && (
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} layout="vertical" margin={{ left: 24, right: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#2a3648" />
                  <XAxis type="number" stroke="#9aabbf" hide />
                  <YAxis type="category" dataKey="name" width={90} stroke="#9aabbf" tick={{ fontSize: 10 }} />
                  <Tooltip
                    contentStyle={{ background: "#121821", border: "1px solid #2a3648" }}
                    formatter={(value) => formatDps(Number(value))}
                  />
                  <Bar dataKey="dps" fill="#d4a54a" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          <div className="max-h-48 overflow-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-[var(--muted)]">
                <tr>
                  <th className="py-1">Способность</th>
                  <th>% </th>
                  <th>DPS</th>
                  <th>Casts</th>
                </tr>
              </thead>
              <tbody>
                {result.breakdown.slice(0, 15).map((row) => (
                  <tr key={row.name} className="border-t border-[var(--line)]">
                    <td className="py-1 pr-2">{row.name}</td>
                    <td>{row.pctTotal.toFixed(1)}</td>
                    <td>{formatDps(row.dps ?? 0)}</td>
                    <td>{row.casts.toFixed(0)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {(result.assumptions?.length || result.warnings.length > 0) && (
            <div className="space-y-1 text-xs">
              <div className="label">Допущения / предупреждения</div>
              {(result.assumptions ?? []).map((a) => (
                <div key={a} className="text-[var(--muted)]">
                  • {a}
                </div>
              ))}
              {result.warnings.map((w) => (
                <div key={w} className="text-amber-200">
                  ⚠ {w}
                </div>
              ))}
            </div>
          )}

          <div className="text-[10px] text-[var(--muted)]">
            engine={result.engine} · snapshot={result.dataSnapshotId}
            {result.hotfixDate ? ` · hotfix=${result.hotfixDate}` : ""}
            {result.clientBuild ? ` · build=${result.clientBuild}` : ""}
          </div>
        </div>
      )}

      {store.compareResult && (
        <div className="rounded-xl border border-[var(--line)] p-3 text-sm">
          <div className="label">Сравнение</div>
          <div>
            A {formatDps(store.compareResult.dpsA)} → B {formatDps(store.compareResult.dpsB)} (
            {store.compareResult.percentDiff.toFixed(2)}%)
          </div>
          <div className="text-xs text-[var(--muted)]">{store.compareResult.note}</div>
        </div>
      )}
    </aside>
  );
}
