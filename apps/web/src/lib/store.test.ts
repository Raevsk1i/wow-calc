import { beforeEach, describe, expect, it } from "vitest";

import { useSimulatorStore } from "@/lib/store";

describe("buildRequest", () => {
  beforeEach(() => {
    useSimulatorStore.setState({
      classId: 5,
      specId: 258,
      heroTalent: "archon",
      talentString: "",
      disabledActions: ["power_infusion"],
      priority: [],
      rotationMode: "automatic",
      customApl: "",
      rawSimcProfile: "",
      targets: 5,
      duration: 300,
      fightStyle: "Patchwerk",
      mode: "preview",
      iterations: null,
      seed: 42,
      clusterRadiusYards: 5,
      gearPreset: "high",
      selectedSpec: {
        id: 258,
        classId: 5,
        className: "Priest",
        name: "Shadow",
        role: "DPS",
        resourceType: "Insanity",
        simulationSupport: "supported",
        heroTalentTrees: [],
        abilities: [],
      },
    });
  });

  it("includes raid toggles, mode preview, and seed", () => {
    const req = useSimulatorStore.getState().buildRequest();
    expect(req.specId).toBe(258);
    expect(req.fight).toMatchObject({ targets: 5, duration: 300, mode: "preview" });
    expect(req.raid).toMatchObject({ battleShout: true, arcaneIntellect: true });
    expect(req.seed).toBe(42);
  });

  it("adds tank incoming model for tanks", () => {
    useSimulatorStore.setState({
      selectedSpec: {
        id: 250,
        classId: 6,
        className: "Death Knight",
        name: "Blood",
        role: "TANK",
        resourceType: "Runic Power",
        simulationSupport: "experimental",
        heroTalentTrees: [],
        abilities: [],
      },
      specId: 250,
      tankIncomingEnabled: true,
      tankAps: 1.5,
    });
    const req = useSimulatorStore.getState().buildRequest();
    expect(req.incomingDamageModel).toMatchObject({
      enabled: true,
      attacksPerSecond: 1.5,
    });
  });
});
