# Research ↔ Live PARITY REPORT

Local-only diagnostic. Does **not** change STRATEGY_LOCK / alpha parameters.
Infrastructure-only live alignment to locked research; no STRATEGY_LOCK mutation.

- Cases recorded: **29**
- PARITY: **29**
- Drift counts: `{"PARITY": 29}`

## Summary table

| CASE | equal | difference_type | research_value | live_value | difference | alpha_impact |
|---|---|---|---|---|---|---|
| B01_far_same_dte_delta_diff_volume | True | PARITY | `{'cid': 'HIGH_VOL', 'strike': 451.0}` | `{'cid': 'HIGH_VOL', 'strike': 451.0}` | `{'research_cid': 'HIGH_VOL', 'live_cid': 'HIGH_VOL'}` | No alpha impact — values already match under identical inputs. |
| B02_far_same_except_strike | True | PARITY | `{'cid': 'K450', 'strike': 450.0}` | `{'cid': 'K450', 'strike': 450.0}` | `{'research_cid': 'K450', 'live_cid': 'K450'}` | No alpha impact — values already match under identical inputs. |
| B03_far_missing_volume | True | PARITY | `{'cid': 'V0', 'strike': 460.0}` | `{'cid': 'V0', 'strike': 460.0}` | `{'research_cid': 'V0', 'live_cid': 'V0'}` | No alpha impact — values already match under identical inputs. |
| B04_far_multiple_expiry | True | PARITY | `{'cid': 'E95', 'strike': 450.0}` | `{'cid': 'E95', 'strike': 450.0}` | `{'research_cid': 'E95', 'live_cid': 'E95'}` | No alpha impact — values already match under identical inputs. |
| B05_far_expiry_volume_tiebreak | True | PARITY | `{'cid': 'E95_HIGHVOL', 'strike': 450.0}` | `{'cid': 'E95_HIGHVOL', 'strike': 450.0}` | `{'research_cid': 'E95_HIGHVOL', 'live_cid': 'E95_HIGHVOL'}` | No alpha impact — values already match under identical inputs. |
| A01_gamma_n_lt_3 | True | PARITY | `None` | `None` | `0` | No alpha impact — values already match under identical inputs. |
| A02_gamma_n_eq_3 | True | PARITY | `None` | `None` | `0` | No alpha impact — values already match under identical inputs. |
| A03_gamma_n_eq_4 | True | PARITY | `None` | `None` | `0` | No alpha impact — values already match under identical inputs. |
| A04_gamma_n_eq_5 | True | PARITY | `30.0` | `30.0` | `0` | No alpha impact — values already match under identical inputs. |
| A05_gamma_n_eq_20 | True | PARITY | `10.5` | `10.5` | `0` | No alpha impact — values already match under identical inputs. |
| A06_gamma_n_gt_20 | True | PARITY | `15.5` | `15.5` | `0` | No alpha impact — values already match under identical inputs. |
| A07_gamma_constant | True | PARITY | `5.0` | `5.0` | `0` | No alpha impact — values already match under identical inputs. |
| A08_gamma_jumping | True | PARITY | `50.5` | `50.5` | `0` | No alpha impact — values already match under identical inputs. |
| A09_gamma_missing_none | True | PARITY | `4.0` | `4.0` | `0` | No alpha impact — values already match under identical inputs. |
| A10_schema_gamma_spot_vs_raw_abs | True | PARITY | `6.075` | `6.075` | `0` | No alpha impact — values already match under identical inputs. |
| A11_gamma_history_old_schema_reset | True | PARITY | `{'history': [], 'schema': 2, 'unit': 'gamma_spot'}` | `{'history': [], 'schema': 2, 'unit': 'gamma_spot'}` | `0` | Infra: discard legacy raw /γ/ warm-up; collect fresh gamma_spot. |
| A12_gamma_history_schema2_keep | True | PARITY | `{'history': [4.0, 4.2, 3.8, 4.1, 4.3, 4.0], 'baseline_ready': True}` | `{'history': [4.0, 4.2, 3.8, 4.1, 4.3, 4.0], 'baseline_ready': True, 'baseline': ` | `0` | Infra: schema2 + unit gamma_spot history retained. |
| A13_gamma_history_missing_unit_reset | True | PARITY | `{'history': [], 'unit': 'gamma_spot'}` | `{'history': [], 'unit': 'gamma_spot'}` | `0` | Infra: missing unit marker forces warm-up reset. |
| C01_near_same_dte_delta_diff_volume | True | PARITY | `{'cid': 'N_HIGH', 'strike': 396.0}` | `{'cid': 'N_HIGH', 'strike': 396.0}` | `{'research_cid': 'N_HIGH', 'live_cid': 'N_HIGH'}` | No alpha impact — values already match under identical inputs. |
| C02_near_same_except_strike | True | PARITY | `{'cid': 'N398', 'strike': 398.0}` | `{'cid': 'N398', 'strike': 398.0}` | `{'research_cid': 'N398', 'live_cid': 'N398'}` | No alpha impact — values already match under identical inputs. |
| C03_near_missing_volume | True | PARITY | `{'cid': 'N_B', 'strike': 399.0}` | `{'cid': 'N_B', 'strike': 399.0}` | `{'research_cid': 'N_B', 'live_cid': 'N_B'}` | No alpha impact — values already match under identical inputs. |
| C04_near_multiple_expiry | True | PARITY | `{'cid': 'N28', 'strike': 398.0}` | `{'cid': 'N28', 'strike': 398.0}` | `{'research_cid': 'N28', 'live_cid': 'N28'}` | No alpha impact — values already match under identical inputs. |
| C05_near_strike_pool_1_02_vs_1_01 | True | PARITY | `{'cid': None, 'strike': None}` | `{'cid': None, 'strike': None}` | `{'research_cid': None, 'live_cid': None}` | No alpha impact — values already match under identical inputs. |
| D01_stack_low_risk | True | PARITY | `{'desired_stack': 1, 'risk_score': 1.0}` | `{'desired_stack': 1, 'risk_score': 1.0}` | `{'stack_delta': 0, 'score_delta': 0.0}` | No alpha impact — values already match under identical inputs. |
| D02_stack_mid_risk | True | PARITY | `{'desired_stack': 4, 'risk_score': 3.3}` | `{'desired_stack': 4, 'risk_score': 3.3}` | `{'stack_delta': 0, 'score_delta': 0.0}` | No alpha impact — values already match under identical inputs. |
| D03_stack_high_risk_boost2 | True | PARITY | `{'desired_stack': 5, 'risk_score': 4.6}` | `{'desired_stack': 5, 'risk_score': 4.6}` | `{'stack_delta': 0, 'score_delta': 0.0}` | No alpha impact — values already match under identical inputs. |
| D04_stack_score_below_3_2 | True | PARITY | `{'desired_stack': 3, 'risk_score': 2.8}` | `{'desired_stack': 3, 'risk_score': 2.8}` | `{'stack_delta': 0, 'score_delta': 0.0}` | No alpha impact — values already match under identical inputs. |
| D05_stack_score_ge_3_2 | True | PARITY | `{'desired_stack': 4, 'risk_score': 3.3}` | `{'desired_stack': 4, 'risk_score': 3.3}` | `{'stack_delta': 0, 'score_delta': 0.0}` | No alpha impact — values already match under identical inputs. |
| D06_stack_zero_gamma_falsy_live | True | PARITY | `5` | `5` | `0` | Live risk_state uses gamma_spot=abs(gamma)*spot; gamma=0 yields gr=0. Aligning LIVE to research preserves locked evidenc |

## Alignment status (infra-only LIVE->RESEARCH)

1. gamma_baseline: research + live both use shift(1)/pre-append + rolling(20, min_periods=5).median() on gamma_spot=abs(gamma)*spot; live stamps gamma_history_schema=2 / unit=gamma_spot and resets legacy raw |γ|.
2. Far/near selection: both two-stage expiry then strike with volume tie-break; live Contract.volume enriched from quotes.
3. Near strike pool: both <=spot*1.02 then final <=spot*1.01.
4. target/desired stack: scoring + ceil coverage; live gamma_rel from gamma_spot / baseline.

## Notes

- Infrastructure-only LIVE->RESEARCH alignment applied (no STRATEGY_LOCK / research alpha edits).
- Do not change research median->mean or drop volume from research — that would be new candidate / evidence invalidation.

