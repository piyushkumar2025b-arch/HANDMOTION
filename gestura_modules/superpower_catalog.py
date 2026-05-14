"""Superpower registry shared by Python tools.

The catalog intentionally mirrors the browser power-pack style: each power has
a pose/motion trigger or a two-hand trigger, an effect family, and a priority.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, Iterable, List, Optional


@dataclass(frozen=True)
class PowerTrigger:
    pose: Optional[str] = None
    motion: Optional[str] = None
    two_hand: Optional[str] = None
    min_confidence: float = 0.0


@dataclass(frozen=True)
class Superpower:
    id: str
    name: str
    trigger: PowerTrigger
    effect: str
    color: str
    cooldown_ms: int = 900
    duration_ms: int = 900
    priority: int = 70
    tags: tuple[str, ...] = ()


_RAW = [
    ("arc_repulsor", "Arc Repulsor", "openPalm", "jab", None, "beam", "#00f5ff", 800, 780, 92, ("attack", "iron")),
    ("photon_shield", "Photon Shield", "openPalm", "hold", None, "shield", "#39ff14", 1300, 1200, 78, ("defense",)),
    ("solar_flare", "Solar Flare", "openPalm", "swipeUp", None, "flare", "#ffb700", 950, 900, 82, ("fire", "area")),
    ("wind_slash", "Wind Slash", "openPalm", "swipeLeft", None, "slash", "#9ef7ff", 850, 720, 80, ("wind",)),
    ("force_push", "Force Push", "openPalm", "swipeRight", None, "wave", "#00f5ff", 850, 760, 80, ("telekinesis",)),
    ("earth_drop", "Earth Drop", "openPalm", "swipeDown", None, "shockwave", "#ff6a00", 950, 900, 79, ("earth",)),
    ("storm_wave", "Storm Wave", "openPalm", "wave", None, "storm", "#b44fff", 1200, 1050, 84, ("electric",)),
    ("vortex_ring", "Vortex Ring", "openPalm", "circleCW", None, "portal", "#00f5ff", 1000, 1100, 86, ("space",)),
    ("nebula_spiral", "Nebula Spiral", "openPalm", "circleCCW", None, "gravity", "#ff006e", 1000, 1100, 86, ("space",)),
    ("plasma_flick", "Plasma Flick", "openPalm", "flick", None, "burst", "#ffe66d", 700, 620, 88, ("plasma",)),
    ("seismic_smash", "Seismic Smash", "fist", "swipeDown", None, "shockwave", "#ff6a00", 950, 930, 84, ("earth",)),
    ("meteor_punch", "Meteor Punch", "fist", "jab", None, "comet", "#ff3300", 780, 760, 91, ("fire", "attack")),
    ("rocket_uppercut", "Rocket Uppercut", "fist", "swipeUp", None, "flame", "#ffb700", 900, 920, 80, ("fire",)),
    ("shadow_dash_left", "Shadow Dash Left", "fist", "swipeLeft", None, "phase", "#8a5cff", 850, 700, 76, ("movement",)),
    ("shadow_dash_right", "Shadow Dash Right", "fist", "swipeRight", None, "phase", "#8a5cff", 850, 700, 76, ("movement",)),
    ("power_charge", "Power Charge", "fist", "hold", None, "charge", "#39ff14", 1250, 1200, 72, ("buff",)),
    ("thunder_shake", "Thunder Shake", "fist", "shake", None, "storm", "#b44fff", 900, 980, 86, ("electric",)),
    ("laser_pointer", "Laser Pointer", "point", "hold", None, "beam", "#ff006e", 950, 900, 77, ("precision",)),
    ("lightning_lance", "Lightning Lance", "point", "jab", None, "storm", "#b44fff", 780, 760, 90, ("electric",)),
    ("railgun_snap", "Railgun Snap", "point", "flick", None, "beam", "#d9fbff", 740, 620, 89, ("precision",)),
    ("time_skip", "Time Skip", "point", "swipeRight", None, "time", "#00f5ff", 950, 920, 80, ("time",)),
    ("rewind_field", "Rewind Field", "point", "swipeLeft", None, "time", "#ff006e", 950, 920, 80, ("time",)),
    ("sky_hook", "Sky Hook", "point", "swipeUp", None, "tether", "#39ff14", 860, 780, 78, ("utility",)),
    ("earth_bind", "Earth Bind", "point", "swipeDown", None, "web", "#ffb700", 860, 820, 78, ("control",)),
    ("orbit_draw", "Orbit Draw", "point", "circleCW", None, "orbit", "#00f5ff", 980, 1080, 83, ("space",)),
    ("reverse_orbit", "Reverse Orbit", "point", "circleCCW", None, "orbit", "#ff006e", 980, 1080, 83, ("space",)),
    ("twin_beam", "Twin Beam", "peace", "jab", None, "beam", "#00f5ff", 780, 760, 89, ("attack",)),
    ("blink_left", "Blink Left", "peace", "swipeLeft", None, "phase", "#9ef7ff", 780, 600, 75, ("movement",)),
    ("blink_right", "Blink Right", "peace", "swipeRight", None, "phase", "#9ef7ff", 780, 600, 75, ("movement",)),
    ("levitation_field", "Levitation Field", "peace", "swipeUp", None, "field", "#39ff14", 900, 980, 76, ("control",)),
    ("descent_field", "Descent Field", "peace", "swipeDown", None, "field", "#ffb700", 900, 980, 76, ("control",)),
    ("charm_field", "Charm Field", "peace", "hold", None, "aura", "#ff4fd8", 1300, 1180, 70, ("aura",)),
    ("duplicate_trail", "Duplicate Trail", "peace", "wave", None, "trail", "#00f5ff", 1050, 1060, 77, ("illusion",)),
    ("portal_open", "Portal Open", "pinch", "hold", None, "portal", "#b44fff", 1200, 1200, 87, ("space",)),
    ("portal_throw", "Portal Throw", "pinch", "flick", None, "portal", "#00f5ff", 780, 900, 90, ("space",)),
    ("reality_thread", "Reality Thread", "pinch", "swipeRight", None, "tether", "#39ff14", 860, 850, 78, ("utility",)),
    ("thread_pull", "Thread Pull", "pinch", "swipeLeft", None, "tether", "#ff006e", 860, 850, 78, ("utility",)),
    ("spark_forge", "Spark Forge", "pinch", "jab", None, "forge", "#ffb700", 760, 760, 86, ("craft",)),
    ("micro_well", "Micro Well", "pinch", "circleCW", None, "gravity", "#00f5ff", 950, 1100, 82, ("gravity",)),
    ("time_knot", "Time Knot", "pinch", "circleCCW", None, "time", "#ff006e", 950, 1100, 82, ("time",)),
    ("sonic_boom", "Sonic Boom", "rock", "jab", None, "wave", "#39ff14", 760, 760, 88, ("sound",)),
    ("amp_wave", "Amp Wave", "rock", "shake", None, "wave", "#ff006e", 880, 920, 83, ("sound",)),
    ("shock_chord", "Shock Chord", "rock", "swipeUp", None, "storm", "#b44fff", 900, 860, 78, ("sound", "electric")),
    ("riff_slash", "Riff Slash", "rock", "swipeRight", None, "slash", "#ffb700", 820, 720, 78, ("sound",)),
    ("drone_swarm", "Drone Swarm", "three", "circleCW", None, "swarm", "#00f5ff", 1050, 1180, 80, ("summon",)),
    ("holo_cube", "Holo Cube", "three", "hold", None, "cube", "#00f5ff", 1300, 1350, 71, ("hologram",)),
    ("tri_beam", "Tri Beam", "three", "jab", None, "beam", "#39ff14", 780, 760, 86, ("attack",)),
    ("ai_scan", "AI Scan", "four", "hold", None, "scan", "#00f5ff", 1300, 1200, 72, ("analytics",)),
    ("data_rain", "Data Rain", "four", "swipeDown", None, "data", "#39ff14", 900, 1000, 77, ("analytics",)),
    ("quantum_grid", "Quantum Grid", "four", "swipeUp", None, "grid", "#00f5ff", 900, 1000, 77, ("grid",)),
    ("energy_net", "Energy Net", "four", "wave", None, "web", "#9ef7ff", 1000, 1030, 77, ("control",)),
    ("heart_burst", "Heart Burst", "love", "hold", None, "heart", "#ff006e", 1300, 1100, 72, ("aura",)),
    ("signal_call", "Signal Call", "phone", "jab", None, "rings", "#39ff14", 850, 900, 78, ("signal",)),
    ("web_caster", "Web Caster", "web", "jab", None, "web", "#d9fbff", 820, 860, 82, ("control",)),
    ("ice_claw", "Ice Claw", "claw", "swipeDown", None, "ice", "#9ef7ff", 920, 950, 78, ("ice",)),
    ("nova_claw", "Nova Claw", "claw", "swipeUp", None, "flare", "#ffb700", 920, 950, 78, ("fire",)),
    ("clap_nova", "Clap Nova", None, None, "clap", "shockwave", "#ffb700", 1200, 1050, 98, ("two-hand",)),
    ("star_gate", "Star Gate", None, None, "expand", "portal", "#b44fff", 1150, 1250, 94, ("two-hand", "space")),
    ("crush_field", "Crush Field", None, None, "compress", "gravity", "#ff006e", 1150, 1250, 94, ("two-hand", "gravity")),
    ("balance_aura", "Balance Aura", None, None, "mirror", "aura", "#39ff14", 1450, 1280, 74, ("two-hand", "aura")),
    ("fusion_core", "Fusion Core", None, None, "palmsTogetherHold", "charge", "#00f5ff", 1500, 1300, 88, ("two-hand", "charge")),
]


POWER_CATALOG: tuple[Superpower, ...] = tuple(
    Superpower(
        id=power_id,
        name=name,
        trigger=PowerTrigger(pose=pose, motion=motion, two_hand=two_hand),
        effect=effect,
        color=color,
        cooldown_ms=cooldown,
        duration_ms=duration,
        priority=priority,
        tags=tags,
    )
    for power_id, name, pose, motion, two_hand, effect, color, cooldown, duration, priority, tags in _RAW
)


def get_power(power_id: str) -> Optional[Superpower]:
    return next((power for power in POWER_CATALOG if power.id == power_id), None)


def search_powers(text: str = "", tag: str | None = None) -> List[Superpower]:
    needle = text.lower().strip()
    results = []
    for power in POWER_CATALOG:
        haystack = " ".join((power.id, power.name, power.effect, *power.tags)).lower()
        if needle and needle not in haystack:
            continue
        if tag and tag not in power.tags:
            continue
        results.append(power)
    return sorted(results, key=lambda power: (-power.priority, power.name))


def match_powers(pose: str | None, motions: Iterable[str], two_hand: Iterable[str] = ()) -> List[Superpower]:
    motion_set = set(motions)
    two_set = set(two_hand)
    matches = []
    for power in POWER_CATALOG:
        trigger = power.trigger
        if trigger.two_hand:
            if trigger.two_hand in two_set:
                matches.append(power)
            continue
        if trigger.pose == pose and trigger.motion in motion_set:
            matches.append(power)
    return sorted(matches, key=lambda power: (-power.priority, power.cooldown_ms, power.name))


def grouped_by_effect() -> Dict[str, List[Superpower]]:
    groups: Dict[str, List[Superpower]] = {}
    for power in POWER_CATALOG:
        groups.setdefault(power.effect, []).append(power)
    return groups


def to_json_ready(powers: Iterable[Superpower] = POWER_CATALOG) -> list[dict]:
    return [asdict(power) for power in powers]

