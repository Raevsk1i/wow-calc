#!/usr/bin/env python3
"""Build the Midnight 12.1.5 catalog with all 40 character specializations.

Parses MID presets for ability tokens when present. Does not invent damage coefficients.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRESETS = ROOT / "packages/game-data/presets/12.1.5"
OUT = ROOT / "packages/game-data/catalog/12.1.5/catalog.json"
RULESET = ROOT / "packages/game-data/catalog/12.1.5/ruleset.json"

# Tokens that are APL control flow / variables, not player abilities.
SKIP_TOKENS = {
    "if",
    "variable",
    "variables",
    "call_action_list",
    "run_action_list",
    "snapshot_stats",
    "use_items",
    "use_item",
    "potion",
    "name",
    "slot",
    "slots",
    "slot1",
    "slot2",
    "target_if",
    "cycle_targets",
    "for_next",
    "line_cd",
    "use_off_gcd",
    "invoke_external_buff",
    "power_infusion",
    "bloodlust",
    "racials",
    "on_gcd_racials",
    "trinkets",
    "items",
    "item",
    "cooldowns",
    "cds",
    "aoe",
    "single_target",
    "main",
    "opener",
    "fallback",
    "default_st",
    "multitarget",
    "patchwerk",
    "high_prio_actions",
    "high_priority",
    "trinket_priority",
    "damage_trinket_priority",
    "trinket",
    "type",
    "toggle",
    "hold",
    "highest",
    "lowest",
    "second",
    "pot",
    "race",
    "chain",
    "ogcd",
    "green",
    "mini",
    "fill",
    "build",
    "finish",
    "spend",
    "generate",
    "stealth",
    "misc_cds",
    "core_dot",
    "apply_poison",
    "kick",
    "disrupt",
    "mind_freeze",
    "adds_remain",
    "variable",
}

CURATED: dict[str, list[dict]] = {
    "death_knight_frost": [
        ("obliterate", "Obliterate", False, "single_target"),
        ("frostscythe", "Frostscythe", True, "aoe"),
        ("howling_blast", "Howling Blast", False, "aoe"),
        ("frost_strike", "Frost Strike", False, "single_target"),
        ("remorseless_winter", "Remorseless Winter", True, "aoe"),
        ("pillar_of_frost", "Pillar of Frost", True, "single_target"),
        ("breath_of_sindragosa", "Breath of Sindragosa", True, "aoe"),
        ("auto_attack", "Auto Attack", False, "single_target"),
    ],
    "death_knight_unholy": [
        ("festering_strike", "Festering Strike", False, "single_target"),
        ("scourge_strike", "Scourge Strike", False, "cleave"),
        ("death_coil", "Death Coil", False, "single_target"),
        ("epidemic", "Epidemic", True, "aoe"),
        ("outbreak", "Outbreak", False, "single_target"),
        ("apocalypse", "Apocalypse", True, "single_target"),
        ("dark_transformation", "Dark Transformation", True, "single_target"),
        ("raise_dead", "Raise Dead", False, "single_target"),
        ("defile", "Defile", True, "aoe"),
        ("auto_attack", "Auto Attack", False, "single_target"),
    ],
    "demon_hunter_havoc": [
        ("chaos_strike", "Chaos Strike", False, "single_target"),
        ("blade_dance", "Blade Dance", False, "aoe"),
        ("death_sweep", "Death Sweep", True, "aoe"),
        ("eye_beam", "Eye Beam", True, "aoe"),
        ("essence_break", "Essence Break", True, "cleave"),
        ("immolation_aura", "Immolation Aura", True, "aoe"),
        ("metamorphosis", "Metamorphosis", True, "single_target"),
        ("throw_glaive", "Throw Glaive", True, "cleave"),
        ("auto_attack", "Auto Attack", False, "single_target"),
    ],
    "demon_hunter_vengeance": [
        ("soul_cleave", "Soul Cleave", False, "cleave"),
        ("spirit_bomb", "Spirit Bomb", True, "aoe"),
        ("fracture", "Fracture", False, "single_target"),
        ("immolation_aura", "Immolation Aura", True, "aoe"),
        ("fel_devastation", "Fel Devastation", True, "aoe"),
        ("fiery_brand", "Fiery Brand", True, "single_target"),
        ("sigil_of_flame", "Sigil of Flame", True, "aoe"),
        ("auto_attack", "Auto Attack", False, "single_target"),
    ],
    "demon_hunter_devourer": [
        ("consume", "Consume", False, "single_target"),
        ("reap", "Reap", False, "cleave"),
        ("void_ray", "Void Ray", False, "aoe"),
        ("collapsing_star", "Collapsing Star", True, "aoe"),
        ("devour", "Devour", True, "single_target"),
        ("cull", "Cull", True, "cleave"),
        ("eradicate", "Eradicate", True, "single_target"),
        ("void_metamorphosis", "Void Metamorphosis", True, "single_target"),
        ("auto_attack", "Auto Attack", False, "single_target"),
    ],
    "druid_balance": [
        ("wrath", "Wrath", False, "single_target"),
        ("starfire", "Starfire", False, "aoe"),
        ("starsurge", "Starsurge", False, "single_target"),
        ("starfall", "Starfall", True, "aoe"),
        ("moonfire", "Moonfire", False, "single_target"),
        ("sunfire", "Sunfire", False, "aoe"),
        ("celestial_alignment", "Celestial Alignment", True, "single_target"),
        ("fury_of_elune", "Fury of Elune", True, "aoe"),
        ("force_of_nature", "Force of Nature", True, "single_target"),
    ],
    "druid_feral": [
        ("shred", "Shred", False, "single_target"),
        ("rake", "Rake", False, "single_target"),
        ("rip", "Rip", False, "single_target"),
        ("ferocious_bite", "Ferocious Bite", False, "single_target"),
        ("thrash", "Thrash", True, "aoe"),
        ("primal_wrath", "Primal Wrath", True, "aoe"),
        ("tigers_fury", "Tiger's Fury", True, "single_target"),
        ("berserk", "Berserk", True, "single_target"),
        ("auto_attack", "Auto Attack", False, "single_target"),
    ],
    "evoker_devastation": [
        ("living_flame", "Living Flame", False, "single_target"),
        ("azure_strike", "Azure Strike", False, "cleave"),
        ("disintegrate", "Disintegrate", False, "single_target"),
        ("pyre", "Pyre", True, "aoe"),
        ("fire_breath", "Fire Breath", True, "aoe"),
        ("eternity_surge", "Eternity Surge", True, "cleave"),
        ("dragonrage", "Dragonrage", True, "single_target"),
        ("deep_breath", "Deep Breath", True, "aoe"),
    ],
    "monk_windwalker": [
        ("tiger_palm", "Tiger Palm", False, "single_target"),
        ("rising_sun_kick", "Rising Sun Kick", False, "single_target"),
        ("fists_of_fury", "Fists of Fury", False, "aoe"),
        ("blackout_kick", "Blackout Kick", False, "single_target"),
        ("spinning_crane_kick", "Spinning Crane Kick", True, "aoe"),
        ("whirling_dragon_punch", "Whirling Dragon Punch", True, "aoe"),
        ("invoke_xuen_the_white_tiger", "Invoke Xuen", True, "single_target"),
        ("slicing_winds", "Slicing Winds", True, "aoe"),
        ("auto_attack", "Auto Attack", False, "single_target"),
    ],
    "priest_shadow": [
        ("mind_blast", "Mind Blast", False, "single_target"),
        ("mind_flay", "Mind Flay", False, "single_target"),
        ("shadow_word_pain", "Shadow Word: Pain", False, "single_target"),
        ("vampiric_touch", "Vampiric Touch", False, "single_target"),
        ("devouring_plague", "Devouring Plague", False, "single_target"),
        ("void_bolt", "Void Bolt", True, "single_target"),
        ("void_eruption", "Void Eruption", True, "aoe"),
        ("shadow_crash", "Shadow Crash", True, "aoe"),
        ("halo", "Halo", True, "aoe"),
    ],
    "rogue_assassination": [
        ("mutilate", "Mutilate", False, "single_target"),
        ("garrote", "Garrote", False, "single_target"),
        ("rupture", "Rupture", False, "single_target"),
        ("envenom", "Envenom", False, "single_target"),
        ("crimson_tempest", "Crimson Tempest", True, "aoe"),
        ("deathmark", "Deathmark", True, "single_target"),
        ("kingsbane", "Kingsbane", True, "single_target"),
        ("vanish", "Vanish", True, "single_target"),
        ("auto_attack", "Auto Attack", False, "single_target"),
    ],
    "rogue_outlaw": [
        ("sinister_strike", "Sinister Strike", False, "single_target"),
        ("pistol_shot", "Pistol Shot", False, "single_target"),
        ("dispatch", "Dispatch", False, "single_target"),
        ("between_the_eyes", "Between the Eyes", False, "single_target"),
        ("blade_flurry", "Blade Flurry", True, "aoe"),
        ("adrenaline_rush", "Adrenaline Rush", True, "single_target"),
        ("roll_the_bones", "Roll the Bones", True, "single_target"),
        ("coup_de_grace", "Coup de Grace", True, "single_target"),
        ("ambush", "Ambush", True, "single_target"),
        ("auto_attack", "Auto Attack", False, "single_target"),
    ],
    "rogue_subtlety": [
        ("backstab", "Backstab", False, "single_target"),
        ("shadowstrike", "Shadowstrike", False, "single_target"),
        ("eviscerate", "Eviscerate", False, "single_target"),
        ("shuriken_storm", "Shuriken Storm", True, "aoe"),
        ("shadow_dance", "Shadow Dance", True, "single_target"),
        ("symbols_of_death", "Symbols of Death", True, "single_target"),
        ("goremaws_bite", "Goremaw's Bite", True, "single_target"),
        ("secret_technique", "Secret Technique", True, "aoe"),
        ("auto_attack", "Auto Attack", False, "single_target"),
    ],
    "shaman_enhancement": [
        ("stormstrike", "Stormstrike", False, "single_target"),
        ("lava_lash", "Lava Lash", False, "cleave"),
        ("crash_lightning", "Crash Lightning", True, "aoe"),
        ("sundering", "Sundering", True, "aoe"),
        ("doom_winds", "Doom Winds", True, "aoe"),
        ("primordial_storm", "Primordial Storm", True, "aoe"),
        ("voltaic_blaze", "Voltaic Blaze", True, "aoe"),
        ("flame_shock", "Flame Shock", False, "single_target"),
        ("auto_attack", "Auto Attack", False, "single_target"),
    ],
    "warlock_affliction": [
        ("agony", "Agony", False, "single_target"),
        ("corruption", "Corruption", False, "single_target"),
        ("unstable_affliction", "Unstable Affliction", False, "single_target"),
        ("malefic_rapture", "Malefic Rapture", False, "aoe"),
        ("shadow_bolt", "Shadow Bolt", False, "single_target"),
        ("summon_darkglare", "Summon Darkglare", True, "single_target"),
        ("malevolence", "Malevolence", True, "single_target"),
        ("haunt", "Haunt", True, "single_target"),
    ],
    "warlock_demonology": [
        ("shadow_bolt", "Shadow Bolt", False, "single_target"),
        ("hand_of_guldan", "Hand of Gul'dan", False, "aoe"),
        ("call_dreadstalkers", "Call Dreadstalkers", False, "single_target"),
        ("summon_demonic_tyrant", "Summon Demonic Tyrant", True, "single_target"),
        ("grimoire_felguard", "Grimoire: Felguard", True, "single_target"),
        ("implosion", "Implosion", True, "aoe"),
        ("power_siphon", "Power Siphon", True, "single_target"),
        ("demonbolt", "Demonbolt", False, "single_target"),
    ],
    "warlock_destruction": [
        ("incinerate", "Incinerate", False, "single_target"),
        ("immolate", "Immolate", False, "single_target"),
        ("chaos_bolt", "Chaos Bolt", False, "single_target"),
        ("conflagrate", "Conflagrate", False, "single_target"),
        ("rain_of_fire", "Rain of Fire", True, "aoe"),
        ("cataclysm", "Cataclysm", True, "aoe"),
        ("summon_infernal", "Summon Infernal", True, "aoe"),
        ("soul_fire", "Soul Fire", True, "single_target"),
    ],
    "warrior_fury": [
        ("rampage", "Rampage", False, "cleave"),
        ("bloodthirst", "Bloodthirst", False, "single_target"),
        ("raging_blow", "Raging Blow", False, "single_target"),
        ("execute", "Execute", False, "single_target"),
        ("recklessness", "Recklessness", True, "single_target"),
        ("avatar", "Avatar", True, "single_target"),
        ("odyns_fury", "Odyn's Fury", True, "aoe"),
        ("thunderous_roar", "Thunderous Roar", True, "aoe"),
        ("auto_attack", "Auto Attack", False, "single_target"),
    ],
    "mage_arcane": [
        ("arcane_blast", "Arcane Blast", False, "single_target"),
        ("arcane_missiles", "Arcane Missiles", False, "single_target"),
        ("arcane_barrage", "Arcane Barrage", False, "cleave"),
        ("arcane_surge", "Arcane Surge", True, "aoe"),
        ("arcane_orb", "Arcane Orb", True, "aoe"),
        ("touch_of_the_magi", "Touch of the Magi", True, "single_target"),
        ("presence_of_mind", "Presence of Mind", True, "single_target"),
        ("evocation", "Evocation", True, "single_target"),
    ],
    "mage_fire": [
        ("fireball", "Fireball", False, "single_target"),
        ("pyroblast", "Pyroblast", False, "single_target"),
        ("fire_blast", "Fire Blast", False, "single_target"),
        ("phoenix_flames", "Phoenix Flames", True, "cleave"),
        ("flamestrike", "Flamestrike", True, "aoe"),
        ("combustion", "Combustion", True, "single_target"),
        ("scorch", "Scorch", True, "single_target"),
    ],
    "mage_frost": [
        ("frostbolt", "Frostbolt", False, "single_target"),
        ("ice_lance", "Ice Lance", False, "single_target"),
        ("flurry", "Flurry", False, "single_target"),
        ("frozen_orb", "Frozen Orb", True, "aoe"),
        ("blizzard", "Blizzard", True, "aoe"),
        ("comet_storm", "Comet Storm", True, "aoe"),
        ("icy_veins", "Icy Veins", True, "single_target"),
        ("ray_of_frost", "Ray of Frost", True, "single_target"),
    ],
    "hunter_beast_mastery": [
        ("kill_command", "Kill Command", False, "single_target"),
        ("barbed_shot", "Barbed Shot", False, "single_target"),
        ("cobra_shot", "Cobra Shot", False, "single_target"),
        ("multi_shot", "Multi-Shot", True, "aoe"),
        ("bestial_wrath", "Bestial Wrath", True, "single_target"),
        ("call_of_the_wild", "Call of the Wild", True, "aoe"),
        ("kill_shot", "Kill Shot", True, "single_target"),
        ("dire_beast", "Dire Beast", True, "single_target"),
    ],
    "hunter_marksmanship": [
        ("aimed_shot", "Aimed Shot", False, "single_target"),
        ("rapid_fire", "Rapid Fire", False, "single_target"),
        ("arcane_shot", "Arcane Shot", False, "single_target"),
        ("multi_shot", "Multi-Shot", True, "aoe"),
        ("explosive_shot", "Explosive Shot", True, "aoe"),
        ("trueshot", "Trueshot", True, "single_target"),
        ("kill_shot", "Kill Shot", True, "single_target"),
        ("volley", "Volley", True, "aoe"),
    ],
    "hunter_survival": [
        ("kill_command", "Kill Command", False, "single_target"),
        ("raptor_strike", "Raptor Strike", False, "single_target"),
        ("wildfire_bomb", "Wildfire Bomb", False, "aoe"),
        ("butchery", "Butchery", True, "aoe"),
        ("flanking_strike", "Flanking Strike", True, "single_target"),
        ("coordinated_assault", "Coordinated Assault", True, "single_target"),
        ("kill_shot", "Kill Shot", True, "single_target"),
        ("auto_attack", "Auto Attack", False, "single_target"),
    ],
    "paladin_retribution": [
        ("templar_strike", "Templar Strike", False, "single_target"),
        ("blade_of_justice", "Blade of Justice", False, "single_target"),
        ("judgment", "Judgment", False, "single_target"),
        ("final_verdict", "Final Verdict", False, "single_target"),
        ("divine_storm", "Divine Storm", True, "aoe"),
        ("wake_of_ashes", "Wake of Ashes", True, "aoe"),
        ("avenging_wrath", "Avenging Wrath", True, "single_target"),
        ("auto_attack", "Auto Attack", False, "single_target"),
    ],
    "shaman_elemental": [
        ("lightning_bolt", "Lightning Bolt", False, "single_target"),
        ("lava_burst", "Lava Burst", False, "single_target"),
        ("flame_shock", "Flame Shock", False, "single_target"),
        ("earth_shock", "Earth Shock", False, "single_target"),
        ("earthquake", "Earthquake", True, "aoe"),
        ("chain_lightning", "Chain Lightning", True, "aoe"),
        ("stormkeeper", "Stormkeeper", True, "aoe"),
        ("ascendance", "Ascendance", True, "single_target"),
    ],
    "warrior_arms": [
        ("mortal_strike", "Mortal Strike", False, "single_target"),
        ("overpower", "Overpower", False, "single_target"),
        ("slam", "Slam", False, "single_target"),
        ("execute", "Execute", False, "single_target"),
        ("bladestorm", "Bladestorm", True, "aoe"),
        ("colossus_smash", "Colossus Smash", True, "single_target"),
        ("ravager", "Ravager", True, "aoe"),
        ("auto_attack", "Auto Attack", False, "single_target"),
    ],
}

# Minimal curated lists for tanks/healers/support without MID presets.
ROLE_DEFAULTS: dict[str, list[tuple]] = {
    "death_knight_blood": [
        ("heart_strike", "Heart Strike", False, "cleave"),
        ("blood_boil", "Blood Boil", False, "aoe"),
        ("death_strike", "Death Strike", False, "single_target"),
        ("marrowrend", "Marrowrend", False, "single_target"),
        ("dancing_rune_weapon", "Dancing Rune Weapon", True, "single_target"),
        ("consumption", "Consumption", True, "aoe"),
        ("auto_attack", "Auto Attack", False, "single_target"),
    ],
    "druid_guardian": [
        ("mangle", "Mangle", False, "single_target"),
        ("thrash", "Thrash", False, "aoe"),
        ("moonfire", "Moonfire", False, "single_target"),
        ("maul", "Maul", True, "single_target"),
        ("raze", "Raze", True, "aoe"),
        ("auto_attack", "Auto Attack", False, "single_target"),
    ],
    "druid_restoration": [
        ("wrath", "Wrath", False, "single_target"),
        ("starfire", "Starfire", True, "aoe"),
        ("moonfire", "Moonfire", False, "single_target"),
        ("sunfire", "Sunfire", True, "aoe"),
        ("cat_form_shred", "Shred (Cat)", True, "single_target"),
    ],
    "evoker_preservation": [
        ("living_flame", "Living Flame", False, "single_target"),
        ("fire_breath", "Fire Breath", True, "aoe"),
        ("azure_strike", "Azure Strike", True, "cleave"),
        ("deep_breath", "Deep Breath", True, "aoe"),
    ],
    "evoker_augmentation": [
        ("living_flame", "Living Flame", False, "single_target"),
        ("eruption", "Eruption", False, "aoe"),
        ("fire_breath", "Fire Breath", True, "aoe"),
        ("upheaval", "Upheaval", True, "aoe"),
        ("ebon_might", "Ebon Might", False, "single_target"),
        ("prescience", "Prescience", False, "single_target"),
        ("breath_of_the_eons", "Breath of the Eons", True, "aoe"),
    ],
    "monk_brewmaster": [
        ("keg_smash", "Keg Smash", False, "aoe"),
        ("blackout_kick", "Blackout Kick", False, "single_target"),
        ("tiger_palm", "Tiger Palm", False, "single_target"),
        ("breath_of_fire", "Breath of Fire", True, "aoe"),
        ("rushing_jade_wind", "Rushing Jade Wind", True, "aoe"),
        ("auto_attack", "Auto Attack", False, "single_target"),
    ],
    "monk_mistweaver": [
        ("tiger_palm", "Tiger Palm", False, "single_target"),
        ("rising_sun_kick", "Rising Sun Kick", False, "single_target"),
        ("blackout_kick", "Blackout Kick", False, "single_target"),
        ("spinning_crane_kick", "Spinning Crane Kick", True, "aoe"),
        ("auto_attack", "Auto Attack", False, "single_target"),
    ],
    "paladin_holy": [
        ("judgment", "Judgment", False, "single_target"),
        ("crusader_strike", "Crusader Strike", False, "single_target"),
        ("holy_shock", "Holy Shock", True, "single_target"),
        ("consecration", "Consecration", True, "aoe"),
        ("auto_attack", "Auto Attack", False, "single_target"),
    ],
    "paladin_protection": [
        ("shield_of_the_righteous", "Shield of the Righteous", False, "single_target"),
        ("judgment", "Judgment", False, "single_target"),
        ("avengers_shield", "Avenger's Shield", False, "aoe"),
        ("consecration", "Consecration", False, "aoe"),
        ("hammer_of_the_righteous", "Hammer of the Righteous", False, "aoe"),
        ("auto_attack", "Auto Attack", False, "single_target"),
    ],
    "priest_discipline": [
        ("smite", "Smite", False, "single_target"),
        ("penance", "Penance", False, "single_target"),
        ("shadow_word_pain", "Shadow Word: Pain", False, "single_target"),
        ("holy_nova", "Holy Nova", True, "aoe"),
        ("schism", "Schism", True, "single_target"),
    ],
    "priest_holy": [
        ("smite", "Smite", False, "single_target"),
        ("holy_fire", "Holy Fire", False, "single_target"),
        ("holy_nova", "Holy Nova", True, "aoe"),
        ("holy_word_chastise", "Holy Word: Chastise", True, "single_target"),
    ],
    "shaman_restoration": [
        ("lightning_bolt", "Lightning Bolt", False, "single_target"),
        ("lava_burst", "Lava Burst", False, "single_target"),
        ("flame_shock", "Flame Shock", False, "single_target"),
        ("chain_lightning", "Chain Lightning", True, "aoe"),
    ],
    "warrior_protection": [
        ("shield_slam", "Shield Slam", False, "single_target"),
        ("thunder_clap", "Thunder Clap", False, "aoe"),
        ("revenge", "Revenge", False, "aoe"),
        ("execute", "Execute", True, "single_target"),
        ("avatar", "Avatar", True, "single_target"),
        ("auto_attack", "Auto Attack", False, "single_target"),
    ],
}

HEROES: dict[str, list[dict]] = {
    "priest_shadow": [("archon", "Archon"), ("voidweaver", "Voidweaver")],
    "warlock_affliction": [("hellcaller", "Hellcaller"), ("soul_harvester", "Soul Harvester")],
    "rogue_assassination": [("deathstalker", "Deathstalker"), ("fatebound", "Fatebound")],
    "shaman_enhancement": [("stormbringer", "Stormbringer"), ("totemic", "Totemic")],
    "warrior_fury": [("slayer", "Slayer"), ("mountain_thane", "Mountain Thane")],
    "demon_hunter_havoc": [("aldrachi_reaver", "Aldrachi Reaver"), ("fel_scarred", "Fel-Scarred")],
    "demon_hunter_devourer": [("annihilator", "Annihilator"), ("void_scarred", "Void-Scarred")],
    "death_knight_unholy": [("rider_of_the_apocalypse", "Rider of the Apocalypse"), ("sanlayn", "San'layn")],
    "death_knight_frost": [("deathbringer", "Deathbringer"), ("rider_of_the_apocalypse", "Rider of the Apocalypse")],
    "mage_arcane": [("sunfury", "Sunfury"), ("spellslinger", "Spellslinger")],
    "mage_fire": [("sunfury", "Sunfury"), ("frostfire", "Frostfire")],
    "mage_frost": [("spellslinger", "Spellslinger"), ("frostfire", "Frostfire")],
    "hunter_marksmanship": [("dark_ranger", "Dark Ranger"), ("sentinel", "Sentinel")],
    "hunter_beast_mastery": [("pack_leader", "Pack Leader"), ("dark_ranger", "Dark Ranger")],
    "hunter_survival": [("sentinel", "Sentinel"), ("pack_leader", "Pack Leader")],
    "evoker_augmentation": [("scalecommander", "Scalecommander"), ("chronowarden", "Chronowarden")],
    "evoker_devastation": [("flameshaper", "Flameshaper"), ("scalecommander", "Scalecommander")],
    "paladin_retribution": [("templar", "Templar"), ("herald_of_the_sun", "Herald of the Sun")],
    "warlock_demonology": [("diabolist", "Diabolist"), ("soul_harvester", "Soul Harvester")],
    "warlock_destruction": [("diabolist", "Diabolist"), ("hellcaller", "Hellcaller")],
    "rogue_outlaw": [("fatebound", "Fatebound"), ("trickster", "Trickster")],
    "rogue_subtlety": [("trickster", "Trickster"), ("deathstalker", "Deathstalker")],
    "druid_balance": [("elunes_chosen", "Elune's Chosen"), ("keeper_of_the_grove", "Keeper of the Grove")],
    "druid_feral": [("druid_of_the_claw", "Druid of the Claw"), ("wildstalker", "Wildstalker")],
    "monk_windwalker": [("conduit_of_the_celestials", "Conduit of the Celestials"), ("shado_pan", "Shado-Pan")],
    "shaman_elemental": [("farseer", "Farseer"), ("stormbringer", "Stormbringer")],
    "warrior_arms": [("slayer", "Slayer"), ("colossus", "Colossus")],
}

# class_id, class_en, class_ru, color, specs...
CLASSES = [
    (
        6,
        "Death Knight",
        "Рыцарь смерти",
        "#C41E3A",
        [
            ("death_knight_blood", 250, "Blood", "Кровь", "TANK", "Runic Power", None, "partial"),
            ("death_knight_frost", 251, "Frost", "Лёд", "DPS", "Runic Power", "MID1_Death_Knight_Frost.simc", "implemented"),
            ("death_knight_unholy", 252, "Unholy", "Нечестивость", "DPS", "Runic Power", "MID1_Death_Knight_Unholy.simc", "implemented"),
        ],
    ),
    (
        12,
        "Demon Hunter",
        "Охотник на демонов",
        "#A330C9",
        [
            ("demon_hunter_havoc", 577, "Havoc", "Истребление", "DPS", "Fury", "MID1_Demon_Hunter_Havoc.simc", "implemented"),
            ("demon_hunter_vengeance", 581, "Vengeance", "Месть", "TANK", "Fury", "MID1_Demon_Hunter_Vengeance.simc", "partial"),
            ("demon_hunter_devourer", 1480, "Devourer", "Пожиратель", "DPS", "Fury/Souls", "MID1_Demon_Hunter_Devourer.simc", "implemented"),
        ],
    ),
    (
        11,
        "Druid",
        "Друид",
        "#FF7D0A",
        [
            ("druid_balance", 102, "Balance", "Баланс", "DPS", "Astral Power", "MID1_Druid_Balance.simc", "implemented"),
            ("druid_feral", 103, "Feral", "Сила зверя", "DPS", "Energy/Combo Points", "MID1_Druid_Feral.simc", "implemented"),
            ("druid_guardian", 104, "Guardian", "Страж", "TANK", "Rage", None, "partial"),
            ("druid_restoration", 105, "Restoration", "Исцеление", "HEALER", "Mana", None, "partial"),
        ],
    ),
    (
        13,
        "Evoker",
        "Пробудитель",
        "#33937F",
        [
            ("evoker_devastation", 1467, "Devastation", "Опустошение", "DPS", "Essence", "MID1_Evoker_Devastation.simc", "implemented"),
            ("evoker_preservation", 1468, "Preservation", "Сохранение", "HEALER", "Essence", None, "partial"),
            ("evoker_augmentation", 1473, "Augmentation", "Усиление", "DPS", "Essence", None, "partial"),
        ],
    ),
    (
        3,
        "Hunter",
        "Охотник",
        "#ABD473",
        [
            ("hunter_beast_mastery", 253, "Beast Mastery", "Повелитель зверей", "DPS", "Focus", None, "partial"),
            ("hunter_marksmanship", 254, "Marksmanship", "Стрельба", "DPS", "Focus", None, "partial"),
            ("hunter_survival", 255, "Survival", "Выживание", "DPS", "Focus", None, "partial"),
        ],
    ),
    (
        8,
        "Mage",
        "Маг",
        "#69CCF0",
        [
            ("mage_arcane", 62, "Arcane", "Тайная магия", "DPS", "Mana/Arcane Charges", None, "partial"),
            ("mage_fire", 63, "Fire", "Огонь", "DPS", "Mana", None, "partial"),
            ("mage_frost", 64, "Frost", "Лёд", "DPS", "Mana", None, "partial"),
        ],
    ),
    (
        10,
        "Monk",
        "Монах",
        "#00FF96",
        [
            ("monk_brewmaster", 268, "Brewmaster", "Хмелевар", "TANK", "Energy/Chi", None, "partial"),
            ("monk_mistweaver", 270, "Mistweaver", "Ткач туманов", "HEALER", "Mana/Chi", None, "partial"),
            ("monk_windwalker", 269, "Windwalker", "Танцующий с ветром", "DPS", "Energy/Chi", "MID1_Monk_Windwalker.simc", "implemented"),
        ],
    ),
    (
        2,
        "Paladin",
        "Паладин",
        "#F58CBA",
        [
            ("paladin_holy", 65, "Holy", "Свет", "HEALER", "Mana", None, "partial"),
            ("paladin_protection", 66, "Protection", "Защита", "TANK", "Mana/Holy Power", None, "partial"),
            ("paladin_retribution", 70, "Retribution", "Воздаяние", "DPS", "Holy Power", None, "partial"),
        ],
    ),
    (
        5,
        "Priest",
        "Жрец",
        "#FFFFFF",
        [
            ("priest_discipline", 256, "Discipline", "Послушание", "HEALER", "Mana", None, "partial"),
            ("priest_holy", 257, "Holy", "Свет", "HEALER", "Mana", None, "partial"),
            ("priest_shadow", 258, "Shadow", "Тьма", "DPS", "Insanity", "MID1_Priest_Shadow.simc", "verified"),
        ],
    ),
    (
        4,
        "Rogue",
        "Разбойник",
        "#FFF569",
        [
            ("rogue_assassination", 259, "Assassination", "Ликвидация", "DPS", "Energy/Combo Points", "MID1_Rogue_Assassination.simc", "verified"),
            ("rogue_outlaw", 260, "Outlaw", "Головорез", "DPS", "Energy/Combo Points", "MID1_Rogue_Outlaw.simc", "implemented"),
            ("rogue_subtlety", 261, "Subtlety", "Скрытность", "DPS", "Energy/Combo Points", "MID1_Rogue_Subtlety.simc", "implemented"),
        ],
    ),
    (
        7,
        "Shaman",
        "Шаман",
        "#0070DE",
        [
            ("shaman_elemental", 262, "Elemental", "Стихии", "DPS", "Maelstrom", None, "partial"),
            ("shaman_enhancement", 263, "Enhancement", "Совершенствование", "DPS", "Maelstrom", "MID1_Shaman_Enhancement.simc", "verified"),
            ("shaman_restoration", 264, "Restoration", "Исцеление", "HEALER", "Mana", None, "partial"),
        ],
    ),
    (
        9,
        "Warlock",
        "Чернокнижник",
        "#9482C9",
        [
            ("warlock_affliction", 265, "Affliction", "Колдовство", "DPS", "Soul Shards", "MID1_Warlock_Affliction.simc", "verified"),
            ("warlock_demonology", 266, "Demonology", "Демонология", "DPS", "Soul Shards", "MID1_Warlock_Demonology.simc", "implemented"),
            ("warlock_destruction", 267, "Destruction", "Разрушение", "DPS", "Soul Shards", "MID1_Warlock_Destruction.simc", "implemented"),
        ],
    ),
    (
        1,
        "Warrior",
        "Воин",
        "#C79C6E",
        [
            ("warrior_arms", 71, "Arms", "Оружие", "DPS", "Rage", None, "partial"),
            ("warrior_fury", 72, "Fury", "Неистовство", "DPS", "Rage", "MID1_Warrior_Fury.simc", "implemented"),
            ("warrior_protection", 73, "Protection", "Защита", "TANK", "Rage", None, "partial"),
        ],
    ),
]

NOTES = {
    "demon_hunter_devourer": (
        "Midnight third DH spec. Dual Fury/Souls resource loop: Consume → Reap → Void Ray → "
        "Void Metamorphosis → Collapsing Star. Prefer Annihilator; Void-Scarred reworked in 12.1.5."
    ),
    "mage_arcane": (
        "Arcane Charges + mana conserve/burst model. Accurate simulation requires a MID preset on the "
        "pinned SimC; until imported, Fast Estimate uses curated rotation weights. Status: partial."
    ),
    "evoker_augmentation": (
        "Personal DPS alone understates contribution. Ally attribution requires party model inputs; "
        "without allies the UI shows Personal DPS only with a completeness warning."
    ),
    "death_knight_unholy": (
        "Uses current Lesser Ghoul / disease / pet cleave model from pinned SimC MID1 Unholy profile."
    ),
    "hunter_marksmanship": (
        "Blood Fletching / Apex crit interactions depend on selected talents in the SimC profile."
    ),
    "warrior_fury": (
        "MID1 talents= hash may fail init on pin; engine retries with hero_talents=."
    ),
    "demon_hunter_havoc": (
        "MID1 talents= hash may fail init on pin; engine retries with hero_talents=."
    ),
}


def ability_rows(key: str) -> list[dict]:
    rows = CURATED.get(key) or ROLE_DEFAULTS.get(key) or []
    out = []
    for item in rows:
        aid, name, optional, aoe = item
        out.append(
            {
                "id": aid,
                "name": name,
                "nameRu": name,
                "simcAction": aid,
                "category": "active",
                "optional": optional,
                "aoeClass": aoe,
                "dataStatus": "implemented",
            }
        )
    return out


def hero_rows(key: str) -> list[dict]:
    return [
        {"id": hid, "name": hname, "simcToken": hid}
        for hid, hname in HEROES.get(key, [])
    ]


def main() -> None:
    ruleset = json.loads(RULESET.read_text(encoding="utf-8"))
    classes_out = []
    for class_id, name_en, name_ru, color, specs in CLASSES:
        spec_objs = []
        for key, sid, s_en, s_ru, role, resource, preset, readiness in specs:
            abilities = ability_rows(key)
            heroes = hero_rows(key)
            default_hero = heroes[0]["id"] if heroes else None
            if preset and not (PRESETS / preset).is_file():
                readiness = "unsupported" if readiness != "partial" else "partial"
                preset = None
            # Accurate runnable when preset exists and readiness != unsupported
            can_accurate = bool(preset) and readiness in {"verified", "implemented", "partial"}
            if not preset:
                can_accurate = False
                if readiness in {"verified", "implemented"}:
                    readiness = "partial"
            notes = NOTES.get(key)
            if role == "HEALER" and not notes:
                notes = "Healer DPS requires damageActivityShare; damage-only results are labeled explicitly."
            if role == "TANK" and not notes:
                notes = "Offensive tank simulation; incoming-damage procs depend on encounter settings."
            if key == "evoker_augmentation":
                notes = NOTES[key]
            spec_objs.append(
                {
                    "id": sid,
                    "key": key,
                    "name": s_en,
                    "nameRu": s_ru,
                    "role": role,
                    "attackType": "ranged"
                    if key
                    in {
                        "druid_balance",
                        "evoker_devastation",
                        "evoker_augmentation",
                        "evoker_preservation",
                        "hunter_beast_mastery",
                        "hunter_marksmanship",
                        "mage_arcane",
                        "mage_fire",
                        "mage_frost",
                        "priest_shadow",
                        "priest_discipline",
                        "priest_holy",
                        "shaman_elemental",
                        "warlock_affliction",
                        "warlock_demonology",
                        "warlock_destruction",
                        "demon_hunter_devourer",
                    }
                    else "melee",
                    "primaryStat": "intellect"
                    if any(
                        x in key
                        for x in (
                            "mage_",
                            "priest_",
                            "warlock_",
                            "evoker_",
                            "shaman_elemental",
                            "shaman_restoration",
                            "druid_balance",
                            "druid_restoration",
                            "monk_mistweaver",
                            "paladin_holy",
                        )
                    )
                    else "agility"
                    if any(
                        x in key
                        for x in (
                            "rogue_",
                            "hunter_",
                            "monk_",
                            "druid_feral",
                            "druid_guardian",
                            "demon_hunter_",
                            "shaman_enhancement",
                        )
                    )
                    else "strength",
                    "resourceType": resource,
                    "readiness": readiness,
                    "simulationSupport": readiness,  # new canonical field name shared with API
                    "canAccurate": can_accurate,
                    "canFastEstimate": True,
                    "presetProfile": preset,
                    "defaultHeroTalent": default_hero,
                    "notes": notes,
                    "heroTalentTrees": heroes,
                    "abilities": abilities,
                    "allyModelRequired": key == "evoker_augmentation",
                    "damageActivityShareDefault": 0.3 if role == "HEALER" else 1.0,
                    "offenseTank": role == "TANK",
                }
            )
        classes_out.append(
            {
                "id": class_id,
                "name": name_en,
                "nameRu": name_ru,
                "color": color,
                "specs": spec_objs,
            }
        )

    catalog = {
        "gameVersion": ruleset["patch"],
        "dataSnapshotId": ruleset["dataRevision"],
        "simcCommit": ruleset["simcCommit"],
        "clientBuild": ruleset["clientBuild"],
        "hotfixDate": ruleset["hotfixDate"],
        "region": ruleset["region"],
        "verifiedAt": ruleset["verifiedAt"],
        "confidence": ruleset["confidence"],
        "aplRevision": ruleset["aplRevision"],
        "sources": ruleset["source"],
        "classes": classes_out,
    }

    # Validate counts
    n_classes = len(classes_out)
    n_specs = sum(len(c["specs"]) for c in classes_out)
    keys = [s["key"] for c in classes_out for s in c["specs"]]
    ids = [s["id"] for c in classes_out for s in c["specs"]]
    assert n_classes == 13, n_classes
    assert n_specs == 40, n_specs
    assert len(keys) == len(set(keys))
    assert len(ids) == len(set(ids))

    OUT.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    web_public = ROOT / "apps/web/public/game-catalog.json"
    if web_public.parent.is_dir():
        web_public.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Synced UI fallback catalog → {web_public}")
    print(f"Wrote {OUT} classes={n_classes} specs={n_specs}")


if __name__ == "__main__":
    main()
