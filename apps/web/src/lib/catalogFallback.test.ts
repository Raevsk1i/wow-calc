import { describe, expect, it } from "vitest";

import { mapCatalogToClasses } from "@/lib/catalogFallback";

describe("mapCatalogToClasses", () => {
  it("maps 13/40 registry shape for the picker", () => {
    const classes = mapCatalogToClasses({
      classes: [
        {
          id: 8,
          name: "Mage",
          nameRu: "Маг",
          color: "#69CCF0",
          specs: [
            {
              id: 62,
              key: "mage_arcane",
              name: "Arcane",
              nameRu: "Тайная магия",
              role: "DPS",
              readiness: "partial",
              simulationSupport: "partial",
              abilities: [{ id: "arcane_blast", name: "Arcane Blast", simcAction: "arcane_blast" }],
              heroTalentTrees: [{ id: "sunfury", name: "Sunfury", simcToken: "sunfury" }],
            },
          ],
        },
      ],
    });
    expect(classes).toHaveLength(1);
    expect(classes[0].specs[0].key).toBe("mage_arcane");
    expect(classes[0].specs[0].abilities[0].simcAction).toBe("arcane_blast");
  });
});
