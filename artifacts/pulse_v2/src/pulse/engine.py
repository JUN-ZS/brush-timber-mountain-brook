from __future__ import annotations

"""Reference engine. Compute-heavy scan is allowed.

It must not: unlock Evolution/Capital/LIVE, claim Frozen OOS,
write fitness, or treat NEXT_OPEN as default.
"""

import hashlib
import json
from pathlib import Path

import pandas as pd

from .cost import true_cost_frac
from .event import PulseEvent
from .execution import propose_fills
from .family import collapse, family_id
from .gates import GateLockedError, deny_fitness_backflow
from .harvest import harvest_plan, path_stats
from .journal import JournalRow, prediction_error
from .kill import attack_event, summarize
from .radar import detect_transitions, enrich_states
from .splits import assign_split


ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "data_market_data.csv"
PROTO = ROOT / "protocol" / "pulse_capture.v2.json"


def protocol_hash() -> str:
    raw = json.loads(PROTO.read_text())
    blob = json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(blob).hexdigest()


def load_panel() -> pd.DataFrame:
    df = pd.read_csv(PANEL)
    drop = [c for c in df.columns if c.startswith("fwd")]
    df = df.drop(columns=drop, errors="ignore")
    return df


class PulseV2Engine:
    def __init__(self) -> None:
        self.protocol_hash = protocol_hash()
        self.events: list[PulseEvent] = []
        self.journal: list[dict] = []
        self.attacks: list[dict] = []

    def run_scan(self, max_events: int | None = None) -> dict:
        df = enrich_states(load_panel())
        trans = detect_transitions(df)
        if max_events is not None:
            trans = trans[:max_events]
        cost1 = true_cost_frac(mult=1)
        for n, t in enumerate(trans):
            split = assign_split(t.bar_date, seen_by_tuning=False)
            fam = family_id(t.skeleton, t.direction, t.states["regime"])
            ev = PulseEvent(
                event_id=f"PULSE-{t.bar_date}-{n:05d}",
                bar_date=t.bar_date,
                split=split.name,
                search_level=t.search_level,
                direction=t.direction,
                skeleton=t.skeleton,
                regime=t.states["regime"],
                family_id=fam,
                what_changed=t.what_changed,
                why_unusual=t.why_unusual,
                transition_strength=t.strength,
                states=t.states,
                observed_fields=t.observed,
                missing_fields=t.missing,
                protocol_hash=self.protocol_hash,
                typical_duration="research_5_to_10_bars",
                invalidation="giveback_half_mfe_or_mae_2pct",
                pre_confirmation_loss=0.02,
                harvest_zones=[0.01, 0.02, 0.03],
                runner_rule="only_if_mfe_over_cost_and_not_decayed",
                death_rule="cost_x3_or_crisis_asymmetry_fail",
                evidence_tag=split.evidence_tag,
            )
            ev.asymmetry = max(0.0, t.strength / 1.2)
            self.events.append(ev)

            fills = propose_fills(df, t.i)
            # compare families; do not pick a champion
            family_rows = []
            for fill in fills:
                if fill.fill_price is None or fill.fill_date is None:
                    family_rows.append({"family": fill.family, "status": fill.status, "honesty": fill.honesty})
                    continue
                fill_i = int(df.index[df["Date"].astype(str).str[:10] == fill.fill_date][0])
                stats = path_stats(df, fill_i, t.direction, horizon=10)
                if stats is None:
                    continue
                plan = harvest_plan(stats, cost1)
                att = attack_event(
                    stats.mfe,
                    stats.mae,
                    split.name,
                    ev.regime,
                    n_paths=1,
                    end_ret=stats.end_ret,
                    decayed=stats.decayed,
                    time_to_mfe=stats.time_to_mfe,
                )
                att["event_id"] = ev.event_id
                att["execution_family"] = fill.family
                self.attacks.append(att)
                row = JournalRow(
                    event_id=ev.event_id,
                    event_class=t.skeleton,
                    signal_fingerprint=fam,
                    market_state_snapshot=t.states,
                    entry_reason=t.what_changed,
                    expected_continuation="unknown_class_prior",
                    expected_duration="<=10 bars",
                    expected_upside=0.02,
                    expected_downside=-0.02,
                    execution_family=fill.family,
                    instrument="SPOT_QQQ",
                    fill={"date": fill.fill_date, "price": fill.fill_price, "status": fill.status},
                    actual_path={
                        "mae": stats.mae,
                        "mfe": stats.mfe,
                        "time_to_mfe": stats.time_to_mfe,
                        "time_to_mae": stats.time_to_mae,
                        "time_to_failure": stats.time_to_failure,
                        "end_ret": stats.end_ret,
                        "decayed": stats.decayed,
                    },
                    MAE=stats.mae,
                    MFE=stats.mfe,
                    harvest_actions=[plan],
                    runner_duration=None if not plan["runner_allowed"] else stats.holding_bars,
                    exit_reason=plan["reason"],
                    slippage=fill.missed_move,
                    liquidity=t.states.get("liq"),
                    prediction_error=prediction_error(0.02, stats.mfe),
                    data_split=split.name,
                    protocol_hash=self.protocol_hash,
                    evidence_tag="Hypothetical",
                )
                self.journal.append(row.to_dict())
                family_rows.append({"family": fill.family, "mfe": stats.mfe, "mae": stats.mae, "verdict": att["verdict"]})
            ev.notes["execution_comparison"] = family_rows

        fam = collapse([e.to_dict() for e in self.events])
        kill = summarize(self.attacks)
        return {
            "protocol_hash": self.protocol_hash,
            "n_transitions": len(trans),
            "n_events": len(self.events),
            "n_journal": len(self.journal),
            "family_collapse": {"n_events": fam["n_events"], "n_families": fam["n_families"]},
            "kill_summary": kill,
            "split_counts": _count([e.split for e in self.events]),
            "level_counts": _count([e.search_level for e in self.events]),
            "locks": ["Evolution", "Capital", "FINAL_OOS", "LIVE", "Survival_v1"],
            "claims_forbidden": [
                "this_is_not_frozen_oos",
                "next_open_is_not_default",
                "no_edge_claimed",
                "no_fitness_written",
            ],
        }

    def write_fitness_to_gene(self, *_a, **_k) -> None:
        deny_fitness_backflow("gene.fitness")

    def unlock_evolution(self) -> None:
        raise GateLockedError("Evolution")


def _count(xs: list[str]) -> dict[str, int]:
    d: dict[str, int] = {}
    for x in xs:
        d[x] = d.get(x, 0) + 1
    return d


if __name__ == "__main__":
    eng = PulseV2Engine()
    report = eng.run_scan()
    out = ROOT / "reports" / "pulse_v2_scan.json"
    out.write_text(json.dumps(report, indent=2))
    jout = ROOT / "reports" / "pulse_v2_journal_head.json"
    jout.write_text(json.dumps(eng.journal[:25], indent=2))
    print(json.dumps(report, indent=2))
