from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class ReadinessStatus(str, Enum):
    verified = "verified"
    implemented = "implemented"
    partial = "partial"
    unsupported = "unsupported"


# Backward-compatible alias used by older callers / tests.
SimulationSupport = ReadinessStatus


class Role(str, Enum):
    dps = "DPS"
    tank = "TANK"
    healer = "HEALER"


class AbilityCategory(str, Enum):
    active = "active"
    passive = "passive"
    proc = "proc"
    system = "system"
    required = "required"


class RotationMode(str, Enum):
    automatic = "automatic"
    custom = "custom"
    burst_focus = "burst_focus"
    sustained = "sustained"
    aoe_optimization = "aoe_optimization"


class FightStyle(str, Enum):
    patchwerk = "Patchwerk"
    light_movement = "LightMovement"
    heavy_movement = "HeavyMovement"
    dungeon_slice = "DungeonSlice"
    casting_patchwerk = "CastingPatchwerk"
    low_target_cleave = "LightMovement"
    dungeon_pack = "DungeonSlice"
    large_aoe = "DungeonSlice"
    custom = "Patchwerk"


class SimulationMode(str, Enum):
    fast_estimate = "fast_estimate"
    quick = "quick"  # legacy alias → Accurate with low iterations
    accurate = "accurate"


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"


class HeroTalentTree(BaseModel):
    id: str
    name: str
    simcToken: str | None = None


class Ability(BaseModel):
    id: str
    spellId: int | None = None
    name: str
    nameRu: str | None = None
    simcAction: str
    category: AbilityCategory = AbilityCategory.active
    resourceCost: str | None = None
    cooldown: float | None = None
    castTime: float | None = None
    charges: int | None = None
    aoeClass: str = "single_target"  # single_target | aoe | cleave
    optional: bool = True
    description: str | None = None
    dataStatus: str | None = None


class TalentNode(BaseModel):
    id: int
    name: str
    nameRu: str | None = None
    maxRanks: int = 1
    row: int = 0
    col: int = 0
    tree: str = "spec"  # class | spec | hero | apex
    choiceIndex: int | None = None
    spellId: int | None = None
    prerequisites: list[int] = Field(default_factory=list)
    description: str | None = None


class TalentTree(BaseModel):
    classNodes: list[TalentNode] = Field(default_factory=list)
    specNodes: list[TalentNode] = Field(default_factory=list)
    apexNodes: list[TalentNode] = Field(default_factory=list)
    heroTrees: list[HeroTalentTree] = Field(default_factory=list)


class Specialization(BaseModel):
    id: int
    key: str
    classId: int
    className: str
    classNameRu: str | None = None
    name: str
    nameRu: str | None = None
    role: Role
    attackType: str = "melee"
    primaryStat: str = "agility"
    resourceType: str
    heroTalentTrees: list[HeroTalentTree] = Field(default_factory=list)
    abilities: list[Ability] = Field(default_factory=list)
    talentTree: TalentTree = Field(default_factory=TalentTree)
    simulationSupport: ReadinessStatus
    readiness: ReadinessStatus | None = None
    canAccurate: bool = False
    canFastEstimate: bool = True
    presetProfile: str | None = None
    defaultHeroTalent: str | None = None
    notes: str | None = None
    allyModelRequired: bool = False
    damageActivityShareDefault: float = 1.0
    offenseTank: bool = False

    @model_validator(mode="after")
    def sync_readiness(self) -> Specialization:
        if self.readiness is None:
            self.readiness = self.simulationSupport
        return self


class WowClass(BaseModel):
    id: int
    name: str
    nameRu: str | None = None
    color: str
    specs: list[Specialization] = Field(default_factory=list)


class TalentLoadout(BaseModel):
    exportString: str | None = None
    heroTalent: str | None = None
    selectedNodeIds: list[int] = Field(default_factory=list)
    useProfileTalents: bool = True


class CharacterStats(BaseModel):
    itemLevel: int | None = None
    primaryStat: int | None = None
    crit: int | None = None
    haste: int | None = None
    mastery: int | None = None
    versatility: int | None = None


class GearConfig(BaseModel):
    preset: str = "high"  # entry | mid | high | custom
    customStats: CharacterStats | None = None
    rawSimcProfile: str | None = None
    trinket1Id: int | None = None
    trinket2Id: int | None = None
    tierPieces: int | None = None


class RaidBuffsConfig(BaseModel):
    arcaneIntellect: bool = True
    battleShout: bool = True
    markOfTheWild: bool = True
    skyfury: bool = True
    bloodlust: bool = True
    bloodlustAtMs: int = 0
    powerWordFortitude: bool = True
    chaosBrand: bool = True
    mysticTouch: bool = True


class AllyModelConfig(BaseModel):
    enabled: bool = False
    allyCount: int = 4
    allyMeanDps: float = 50000.0
    buffUptime: float = 0.85


class FightConfig(BaseModel):
    targets: int = 1
    duration: int = 300
    fightStyle: FightStyle = FightStyle.patchwerk
    targetLevel: int | None = None
    movement: bool = False
    latencyMs: int = 50
    mode: SimulationMode = SimulationMode.fast_estimate
    iterations: int | None = None
    clusterRadiusYards: float = 5.0
    addWaves: bool = False
    encounterPreset: str = "boss_patchwerk"
    damageActivityShare: float | None = None
    incomingDamage: bool = False
    raid: RaidBuffsConfig = Field(default_factory=RaidBuffsConfig)
    allies: AllyModelConfig = Field(default_factory=AllyModelConfig)

    @field_validator("targets")
    @classmethod
    def validate_targets(cls, v: int) -> int:
        if v < 1 or v > 20:
            raise ValueError("targets must be between 1 and 20")
        return v

    @field_validator("duration")
    @classmethod
    def validate_duration(cls, v: int) -> int:
        if v < 30 or v > 600:
            raise ValueError("duration must be between 30 and 600 seconds")
        return v


class RotationConfig(BaseModel):
    mode: RotationMode = RotationMode.automatic
    disabledActions: list[str] = Field(default_factory=list)
    priority: list[str] = Field(default_factory=list)
    customApl: str | None = None
    cooldownPolicy: str = "apl"


class SimulationRequest(BaseModel):
    gameVersion: str = "12.1.5"
    specId: int | None = None
    specKey: str | None = None
    talents: TalentLoadout = Field(default_factory=TalentLoadout)
    gear: GearConfig = Field(default_factory=GearConfig)
    rotation: RotationConfig = Field(default_factory=RotationConfig)
    fight: FightConfig = Field(default_factory=FightConfig)
    seed: int | None = None

    @model_validator(mode="after")
    def require_spec(self) -> SimulationRequest:
        if self.specId is None and not self.specKey:
            raise ValueError("specId or specKey is required")
        return self


class AbilityBreakdownRow(BaseModel):
    name: str
    spellId: int | None = None
    damage: float
    pctTotal: float
    casts: float
    avgHit: float | None = None
    dps: float | None = None
    critRate: float | None = None
    directDamage: float | None = None
    periodicDamage: float | None = None


class SimulationResult(BaseModel):
    meanDps: float
    personalDps: float | None = None
    effectiveDps: float | None = None
    allyAttributedDps: float | None = None
    minDps: float | None = None
    maxDps: float | None = None
    medianDps: float | None = None
    stdDev: float | None = None
    meanStdDev: float | None = None
    p05Dps: float | None = None
    p25Dps: float | None = None
    p75Dps: float | None = None
    p95Dps: float | None = None
    confidence95: list[float] | None = None
    totalDamage: float | None = None
    fightLength: float | None = None
    iterations: int | None = None
    targets: int | None = None
    breakdown: list[AbilityBreakdownRow] = Field(default_factory=list)
    actionSequence: list[dict[str, Any]] | None = None
    resourceTimeline: list[dict[str, Any]] | None = None
    buffUptimes: list[dict[str, Any]] | None = None
    gameVersion: str
    simcVersion: str
    simcCommit: str
    dataSnapshotId: str
    clientBuild: int | None = None
    hotfixDate: str | None = None
    sources: list[str] = Field(default_factory=list)
    engine: str
    isDemo: bool = False
    isApproximation: bool = False
    assumptions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class SimulationJobView(BaseModel):
    id: str
    status: JobStatus
    createdAt: str
    updatedAt: str
    request: SimulationRequest
    result: SimulationResult | None = None
    error: str | None = None
    progress: float | None = None


class ComparisonRequest(BaseModel):
    gameVersion: str = "12.1.5"
    fight: FightConfig = Field(default_factory=FightConfig)
    gear: GearConfig = Field(default_factory=GearConfig)
    buildA: SimulationRequest
    buildB: SimulationRequest
    seed: int | None = 417391


class ComparisonResult(BaseModel):
    jobAId: str
    jobBId: str
    dpsA: float
    dpsB: float
    absoluteDiff: float
    percentDiff: float
    significant: bool
    note: str
    breakdownDiff: list[dict[str, Any]] = Field(default_factory=list)


class BuildRecord(BaseModel):
    id: str
    name: str
    createdAt: str
    request: SimulationRequest


class TalentImportRequest(BaseModel):
    exportString: str
    expectedSpecId: int | None = None


class TalentImportResult(BaseModel):
    ok: bool
    specId: int | None = None
    serializationVersion: int | None = None
    exportString: str
    warnings: list[str] = Field(default_factory=list)
    error: str | None = None


class StatWeightsRequest(BaseModel):
    base: SimulationRequest
    deltas: dict[str, int] = Field(
        default_factory=lambda: {"crit": 100, "haste": 100, "mastery": 100, "versatility": 100}
    )


class ExplainRequest(BaseModel):
    result: SimulationResult
    focusAbility: str | None = None


class ApiError(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None
