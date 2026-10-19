from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class SimulationSupport(str, Enum):
    supported = "supported"
    experimental = "experimental"
    partial = "partial"
    unsupported = "unsupported"


class Role(str, Enum):
    dps = "DPS"
    tank = "TANK"
    healer = "HEALER"
    support = "SUPPORT"


class AbilityCategory(str, Enum):
    active = "active"
    passive = "passive"
    proc = "proc"
    system = "system"
    required = "required"


class RotationMode(str, Enum):
    automatic = "automatic"
    custom = "custom"


class FightStyle(str, Enum):
    patchwerk = "Patchwerk"
    light_movement = "LightMovement"
    heavy_movement = "HeavyMovement"
    dungeon_slice = "DungeonSlice"
    casting_patchwerk = "CastingPatchwerk"


class SimulationMode(str, Enum):
    """Dual-mode sim: preview ≈ low-iteration; monte_carlo ≈ final.

    Legacy aliases `quick` / `accurate` remain accepted.
    """

    preview = "preview"
    monte_carlo = "monte_carlo"
    quick = "quick"
    accurate = "accurate"

    def is_final(self) -> bool:
        return self in {SimulationMode.monte_carlo, SimulationMode.accurate}


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
    simcAction: str
    category: AbilityCategory = AbilityCategory.active
    resourceCost: str | None = None
    cooldown: float | None = None
    castTime: float | None = None
    charges: int | None = None
    aoeClass: str = "single_target"  # single_target | aoe | cleave
    optional: bool = True
    description: str | None = None


class TalentNode(BaseModel):
    id: int
    name: str
    maxRanks: int = 1
    row: int = 0
    col: int = 0
    tree: str = "spec"  # class | spec | hero | apex
    choiceIndex: int | None = None
    spellId: int | None = None
    prerequisites: list[int] = Field(default_factory=list)


class TalentTree(BaseModel):
    classNodes: list[TalentNode] = Field(default_factory=list)
    specNodes: list[TalentNode] = Field(default_factory=list)
    heroTrees: list[HeroTalentTree] = Field(default_factory=list)


class SpecCoverage(BaseModel):
    abilities: bool = False
    apl: bool = False
    singleTarget: bool = False
    aoe: bool = False
    pets: bool = False
    apex: bool = False


class AugmentationModel(BaseModel):
    buffFactors: dict[str, float] = Field(default_factory=dict)
    notes: str | None = None


class Specialization(BaseModel):
    id: int
    classId: int
    className: str
    name: str
    canonicalId: str | None = None
    role: Role
    resourceType: str
    heroTalentTrees: list[HeroTalentTree] = Field(default_factory=list)
    abilities: list[Ability] = Field(default_factory=list)
    talentTree: TalentTree = Field(default_factory=TalentTree)
    simulationSupport: SimulationSupport
    presetProfile: str | None = None
    defaultHeroTalent: str | None = None
    notes: str | None = None
    apexNotes: str | None = None
    coverage: SpecCoverage = Field(default_factory=SpecCoverage)
    augmentationModel: AugmentationModel | None = None


class WowClass(BaseModel):
    id: int
    name: str
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


class BloodlustConfig(BaseModel):
    enabled: bool = True
    atMs: int = 0


class RaidConfig(BaseModel):
    """Independent raid buff/debuff toggles — not a single raidDamageMultiplier."""

    arcaneIntellect: bool = True
    battleShout: bool = True
    markOfTheWild: bool = True
    skyfury: bool = True
    chaosBrand: bool = True
    mysticTouch: bool = True
    bloodlust: BloodlustConfig = Field(default_factory=BloodlustConfig)
    optimalRaid: bool | None = None


class IncomingDamageModel(BaseModel):
    enabled: bool = True
    attacksPerSecond: float = 1.2
    physicalFraction: float = 0.75
    magicFraction: float = 0.25


class HealerDamageProfile(BaseModel):
    damageActivity: float = 1.0
    healingActivity: float = 0.0

    @field_validator("damageActivity", "healingActivity")
    @classmethod
    def clamp_activity(cls, v: float) -> float:
        if v < 0 or v > 1:
            raise ValueError("activity must be between 0 and 1")
        return v


class PartyMember(BaseModel):
    specId: int | None = None
    specCanonicalId: str | None = None
    baselineDps: float = Field(gt=0)


class PartyConfig(BaseModel):
    enabled: bool = False
    members: list[PartyMember] = Field(default_factory=list)


class FightConfig(BaseModel):
    targets: int = 1
    duration: int = 300
    fightStyle: FightStyle = FightStyle.patchwerk
    targetLevel: int | None = None
    movement: bool = False
    clusterRadiusYards: float | None = 5.0
    latencyMs: int = 50
    mode: SimulationMode = SimulationMode.preview
    iterations: int | None = None

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


class SimulationRequest(BaseModel):
    gameVersion: str = "12.1.5"
    specId: int
    talents: TalentLoadout = Field(default_factory=TalentLoadout)
    gear: GearConfig = Field(default_factory=GearConfig)
    rotation: RotationConfig = Field(default_factory=RotationConfig)
    fight: FightConfig = Field(default_factory=FightConfig)
    raid: RaidConfig = Field(default_factory=RaidConfig)
    incomingDamageModel: IncomingDamageModel | None = None
    healerDamageProfile: HealerDamageProfile | None = None
    party: PartyConfig | None = None
    seed: int | None = None

    @model_validator(mode="after")
    def normalize_modes(self) -> SimulationRequest:
        # Keep seed on request; fight.seed not used — request.seed is canonical.
        return self


class AbilityBreakdownRow(BaseModel):
    name: str
    spellId: int | None = None
    damage: float
    pctTotal: float
    casts: float
    avgHit: float | None = None
    dps: float | None = None


class SimulationResult(BaseModel):
    meanDps: float
    minDps: float | None = None
    maxDps: float | None = None
    medianDps: float | None = None
    stdDev: float | None = None
    meanStdDev: float | None = None
    p05Dps: float | None = None
    p95Dps: float | None = None
    dpsPerTarget: float | None = None
    personalDps: float | None = None
    externalContributionDps: float | None = None
    effectiveDps: float | None = None
    totalDamage: float | None = None
    fightLength: float | None = None
    iterations: int | None = None
    targets: int | None = None
    breakdown: list[AbilityBreakdownRow] = Field(default_factory=list)
    actionSequence: list[dict[str, Any]] | None = None
    gameVersion: str
    simcVersion: str
    simcCommit: str
    dataSnapshotId: str
    sources: list[str] = Field(default_factory=list)
    engine: str
    isDemo: bool = False
    warnings: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


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


class ApiError(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None
