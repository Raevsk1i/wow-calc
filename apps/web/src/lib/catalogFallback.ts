import type { Spec, WowClass } from "@/lib/api";

/** Map public/game-catalog.json into the UI WowClass shape when the API is unreachable. */
export function mapCatalogToClasses(raw: {
  classes?: Array<{
    id: number;
    name: string;
    nameRu?: string;
    color?: string;
    specs?: Array<Record<string, unknown>>;
  }>;
}): WowClass[] {
  return (raw.classes ?? []).map((c) => ({
    id: c.id,
    name: c.name,
    nameRu: c.nameRu ?? null,
    color: c.color ?? "#888888",
    specs: (c.specs ?? []).map((s) => {
      const readiness = String(s.readiness ?? s.simulationSupport ?? "partial");
      return {
        id: Number(s.id),
        key: String(s.key ?? `${c.name}_${s.name}`).toLowerCase().replace(/\s+/g, "_"),
        classId: c.id,
        className: c.name,
        classNameRu: c.nameRu ?? null,
        name: String(s.name),
        nameRu: (s.nameRu as string | null | undefined) ?? null,
        role: String(s.role ?? "DPS"),
        resourceType: String(s.resourceType ?? "Unknown"),
        simulationSupport: readiness as Spec["simulationSupport"],
        readiness: readiness as Spec["readiness"],
        canAccurate: Boolean(s.canAccurate),
        canFastEstimate: s.canFastEstimate !== false,
        heroTalentTrees: Array.isArray(s.heroTalentTrees)
          ? (s.heroTalentTrees as Spec["heroTalentTrees"])
          : [],
        abilities: Array.isArray(s.abilities)
          ? (s.abilities as Spec["abilities"]).map((a) => ({
              ...a,
              category: a.category ?? "active",
              optional: a.optional ?? true,
              aoeClass: a.aoeClass ?? "single_target",
            }))
          : [],
        notes: (s.notes as string | null | undefined) ?? null,
        defaultHeroTalent: (s.defaultHeroTalent as string | null | undefined) ?? null,
        presetProfile: (s.presetProfile as string | null | undefined) ?? null,
        allyModelRequired: Boolean(s.allyModelRequired),
        damageActivityShareDefault: Number(s.damageActivityShareDefault ?? 1),
        offenseTank: Boolean(s.offenseTank),
        talentTree: {
          classNodes: [],
          specNodes: [],
          apexNodes: [],
          heroTrees: Array.isArray(s.heroTalentTrees)
            ? (s.heroTalentTrees as Spec["heroTalentTrees"])
            : [],
        },
      } satisfies Spec;
    }),
  }));
}

export async function loadFallbackClasses(): Promise<WowClass[]> {
  const res = await fetch("/game-catalog.json", { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`Не удалось загрузить локальный каталог (${res.status})`);
  }
  return mapCatalogToClasses(await res.json());
}
