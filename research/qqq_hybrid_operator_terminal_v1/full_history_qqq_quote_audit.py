#!/usr/bin/env python3
"""Full-history QQQ EOD option quote alignment audit (2018-03-01 through 2025-12-31).

Research-only source/price/IV/liquidity diagnostic; not a portfolio-return replay.
Annual Parquet files are streamed one date at a time after Git-blob SHA validation.
"""
from __future__ import annotations
import hashlib, json, sys, urllib.request
from datetime import date
from collections import defaultdict
from pathlib import Path
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import audit_qqq_public_eod_options as base

START_DATE, END_DATE = "2018-03-01", "2025-12-31"
SOURCE_BASE = "https://raw.githubusercontent.com/anahatsingh-ui/options-dataset-hist/main/qqq"
CACHE_DIR = Path(".cache/qqq-options-full-history")
UNIVERSE_PATH = Path("src/data/universe.json")
MODEL_SOURCE_PATH = Path("research/qqq_hybrid_dynamic_deployment_v1_1_replay.py")
HELPER_SOURCE_PATH = Path("research/qqq_hybrid_operator_terminal_v1/audit_qqq_public_eod_options.py")
UNIVERSE_GIT_BLOB_SHA = "43c1b3053d17b278cfc01bb0b87e41679f3e85c9"
MODEL_SOURCE_GIT_BLOB_SHA = "ac74b3812c826ad491fb829108f26397322e45eb"
HELPER_SOURCE_GIT_BLOB_SHA = "99337743e4133a6905c2904d889cf1b566997e9e"
ANNUAL_FILES = [
 {"year":2018,"name":"options_2018.parquet","bytes":29215815,"sha":"4a130fe579ee141c5836ccaaf093c0cb752ebb19"},
 {"year":2019,"name":"options_2019.parquet","bytes":30998008,"sha":"95386cb37a6b1ca757e7fd6a0b0fd458c91e04ca"},
 {"year":2020,"name":"options_2020.parquet","bytes":59412637,"sha":"9d7abe1144c55e0091d28eca61deec4ac72393a5"},
 {"year":2021,"name":"options_2021.parquet","bytes":74224966,"sha":"3488cffd498a8851861a8dca7d1849a748bc759d"},
 {"year":2022,"name":"options_2022.parquet","bytes":69941736,"sha":"e9bcb16986835e3eba304300aeb6d6a8ed56bbe9"},
 {"year":2023,"name":"options_2023.parquet","bytes":71647343,"sha":"bbaa5aeefc54c76628142a6e95c7424995049063"},
 {"year":2024,"name":"options_2024.parquet","bytes":82434832,"sha":"40c1c2fd986da9b5bcf363cd44c9d5ac3eecc8c3"},
 {"year":2025,"name":"options_2025.parquet","bytes":85765453,"sha":"e92ad6b5c2e757d2c869f747a94853e630142cbf"},
]
UNDERLYING_SPEC = {"name":"underlying_prices.parquet","bytes":332454,"sha":"f3a892bc4c88c692900b5c0071322c6db408996a"}
OPTION_COLUMNS = ["contract_id","symbol","expiration","strike","type","bid","ask","bid_size","ask_size","volume","open_interest","date","implied_volatility","delta"]

def git_blob_sha_bytes(payload):
    h=hashlib.sha1()
    h.update(f"blob {len(payload)}\0".encode("ascii"))
    h.update(payload)
    return h.hexdigest()

def git_blob_sha_file(path, expected_size):
    h=hashlib.sha1()
    h.update(f"blob {expected_size}\0".encode("ascii"))
    with open(path,"rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()

def download_verified(spec, cache):
    cache.mkdir(parents=True,exist_ok=True)
    path=cache/spec["name"]
    if path.exists() and path.stat().st_size==spec["bytes"]:
        sha=git_blob_sha_file(path,spec["bytes"])
        if sha==spec["sha"]:
            return path,{"status":"CACHED_HASH_VERIFIED","bytes":spec["bytes"],"git_blob_sha":sha}
        path.unlink()
    url=SOURCE_BASE+"/"+spec["name"]
    req=urllib.request.Request(url,headers={"User-Agent":"qqq-full-history-option-audit/1.0"})
    h=hashlib.sha1()
    h.update(f"blob {spec['bytes']}\0".encode("ascii"))
    size=0
    with urllib.request.urlopen(req,timeout=120) as resp, path.open("wb") as out:
        while True:
            chunk=resp.read(1024*1024)
            if not chunk: break
            size+=len(chunk);out.write(chunk);h.update(chunk)
    sha=h.hexdigest()
    if size!=spec["bytes"] or sha!=spec["sha"]:
        path.unlink(missing_ok=True)
        raise ValueError(f"{spec['name']} size/SHA mismatch: {size}/{spec['bytes']} bytes, {sha}/{spec['sha']}")
    return path,{"status":"DOWNLOADED_HASH_VERIFIED","bytes":size,"git_blob_sha":sha}

def num(value):
    try:
        x=float(value)
        return x if x==x and abs(x)!=float("inf") else None
    except (TypeError,ValueError):
        return None

def day_string(value):
    return base.as_day(value)

def vix_bucket(value):
    v=num(value)
    if v is None: return "UNKNOWN"
    if v<15: return "LOW_LT15"
    if v<25: return "NORMAL_15_25"
    if v<35: return "ELEVATED_25_35"
    return "HIGH_GTE35"

def summarize_numbers(values):
    xs=sorted(float(x) for x in values if x is not None and num(x) is not None)
    if not xs: return {"n":0,"median":None,"mean":None,"p90":None}
    mid=len(xs)//2
    median=xs[mid] if len(xs)%2 else (xs[mid-1]+xs[mid])/2
    return {"n":len(xs),"median":median,"mean":sum(xs)/len(xs),"p90":xs[min(len(xs)-1,int(.90*(len(xs)-1)))]}

def spread_pct_mid(bid,ask):
    b,a=num(bid),num(ask)
    if b is None or a is None or b<=0 or a<=0 or b>a:return None
    mid=(a+b)/2
    return (a-b)/mid*100 if mid>0 else None

def model_half_spread_fraction(vix):
    """Same VIX-only haircut formula as the preserved QQQ quoteCC proxy."""
    value=num(vix)
    if value is None:return None
    return min(max(0.025+0.08*max(value/100-0.16,0),0.02),0.1)

def pair_metrics(pair,vix):
    if not pair:return None
    obs=num(pair.get("observed_credit_bid_minus_wing_ask"))
    obs_mid=num(pair.get("observed_credit_mid_minus_mid"))
    proxy=pair.get("model_using_raw_close_at_same_listed_strikes") or {}
    chain=pair.get("model_using_raw_close_and_chain_leg_ivs") or {}
    proxy_credit=num(proxy.get("model_conservative_credit"))
    chain_credit=num(chain.get("model_conservative_credit_using_chain_ivs"))
    chain_mid=num(chain.get("model_mid_credit"))
    short_full=num(pair.get("spread_pct_of_short_mid"))
    wing_full=spread_pct_mid(pair.get("wing_bid"),pair.get("wing_ask"))
    model_half=100*model_half_spread_fraction(vix)
    width=num(pair.get("strike_width"))
    return {
      "expiry":pair.get("expiry"),"calendar_dte":pair.get("calendar_dte"),
      "short_contract_id":pair.get("short_contract_id"),"short_strike":num(pair.get("short_strike")),
      "short_delta":num(pair.get("short_delta")),"short_iv":num(pair.get("short_implied_volatility")),
      "short_bid":num(pair.get("short_bid")),"short_ask":num(pair.get("short_ask")),
      "short_volume":num(pair.get("short_volume")),"short_open_interest":num(pair.get("short_open_interest")),
      "wing_contract_id":pair.get("wing_contract_id"),"wing_strike":num(pair.get("wing_strike")),
      "wing_delta":num(pair.get("wing_delta")),"wing_iv":num(pair.get("wing_implied_volatility")),
      "wing_bid":num(pair.get("wing_bid")),"wing_ask":num(pair.get("wing_ask")),
      "wing_volume":num(pair.get("wing_volume")),"wing_open_interest":num(pair.get("wing_open_interest")),
      "strike_width":width,"observed_executable_side_credit":obs,"observed_midpoint_credit":obs_mid,
      "observed_max_loss_per_100_multiplier":(width-obs)*100 if width is not None and obs is not None and 0<obs<width else None,
      "proxy_model_credit_raw_spot":proxy_credit,
      "proxy_model_credit_gap_vs_observed":proxy_credit-obs if proxy_credit is not None and obs is not None else None,
      "chain_iv_model_credit_raw_spot":chain_credit,
      "chain_iv_model_credit_gap_vs_observed":chain_credit-obs if chain_credit is not None and obs is not None else None,
      "chain_iv_model_mid_credit_raw_spot":chain_mid,
      "chain_iv_mid_gap_vs_observed":chain_mid-obs_mid if chain_mid is not None and obs_mid is not None else None,
      "proxy_to_source_iv_ratio_short":num(pair.get("model_to_chain_iv_ratio_short")),
      "proxy_to_source_iv_ratio_wing":num(pair.get("model_to_chain_iv_ratio_wing")),
      "model_half_spread_pct_mid":model_half,
      "observed_short_half_spread_pct_mid":short_full/2 if short_full is not None else None,
      "observed_wing_half_spread_pct_mid":wing_full/2 if wing_full is not None else None,
      "model_haircut_narrower_than_observed_short":model_half is not None and short_full is not None and model_half<short_full/2,
      "model_haircut_narrower_than_observed_wing":model_half is not None and wing_full is not None and model_half<wing_full/2,
    }

def aggregate_rows(rows):
    matched=[r for r in rows if r.get("raw_target_pair")]
    def raw_values(field):
        return [r["raw_target_pair"].get(field) for r in matched if r["raw_target_pair"] and r["raw_target_pair"].get(field) is not None]
    valid_pct=[r.get("valid_two_sided_quote_pct") for r in rows if r.get("valid_two_sided_quote_pct") is not None]
    proxy_gap=raw_values("proxy_model_credit_gap_vs_observed")
    chain_gap=raw_values("chain_iv_model_credit_gap_vs_observed")
    short_ratios=raw_values("proxy_to_source_iv_ratio_short")
    wing_ratios=raw_values("proxy_to_source_iv_ratio_wing")
    return {
      "days_with_chain_rows":len(rows),"days_with_raw_target_pair":len(matched),
      "pair_coverage_pct":100*len(matched)/len(rows) if rows else None,
      "valid_two_sided_quote_pct_median":summarize_numbers(valid_pct),
      "repo_spot_vs_raw_close_pct":summarize_numbers([r.get("repo_spot_vs_raw_close_pct") for r in rows]),
      "proxy_credit_gap_raw_target":summarize_numbers(proxy_gap),
      "proxy_credit_gap_abs":summarize_numbers([abs(x) for x in proxy_gap]),
      "chain_iv_credit_gap_raw_target":summarize_numbers(chain_gap),
      "chain_iv_credit_gap_abs":summarize_numbers([abs(x) for x in chain_gap]),
      "short_delta_abs_error_vs_0p16":summarize_numbers([abs(r["raw_target_pair"]["short_delta"]-.16) for r in matched if r["raw_target_pair"].get("short_delta") is not None]),
      "wing_delta_abs_error_vs_0p08":summarize_numbers([abs(r["raw_target_pair"]["wing_delta"]-.08) for r in matched if r["raw_target_pair"].get("wing_delta") is not None]),
      "proxy_to_source_iv_ratio_short":summarize_numbers(short_ratios),
      "proxy_to_source_iv_ratio_wing":summarize_numbers(wing_ratios),
      "fraction_model_haircut_too_narrow_short":sum(1 for r in matched if r["raw_target_pair"].get("model_haircut_narrower_than_observed_short"))/len(matched) if matched else None,
      "fraction_model_haircut_too_narrow_wing":sum(1 for r in matched if r["raw_target_pair"].get("model_haircut_narrower_than_observed_wing"))/len(matched) if matched else None,
    }

def build_coverage_summary(expected_dates, spots, daily, start_date, end_date):
    """Measure source coverage against the repository's full date index, not only dates with raw spots."""
    expected_set=set(expected_dates)
    spot_dates=set(spots)
    chain_days={r["date"] for r in daily if r.get("option_rows",0)>0}
    pair_days={r["date"] for r in daily if r.get("raw_target_pair")}
    expected_first=min(expected_set) if expected_set else None
    expected_last=max(expected_set) if expected_set else None
    last_spot=max((d for d in spot_dates if start_date<=d<=end_date),default=None)
    last_chain=max((d for d in chain_days if start_date<=d<=end_date),default=None)
    dates_after_spot=[d for d in sorted(expected_set) if last_spot is None or d>last_spot]
    dates_after_chain=[d for d in sorted(expected_set) if last_chain is None or d>last_chain]
    expected_n=len(expected_set)
    chain_in_window=chain_days & expected_set
    pairs_in_window=pair_days & expected_set
    spot_in_window=spot_dates & expected_set
    return {
      "requested_window":{"start":start_date,"end":end_date},
      "expected_trading_dates_from_repo_universe":expected_n,
      "first_expected_trading_date":expected_first,
      "last_expected_trading_date":expected_last,
      "expected_dates_with_raw_underlying_price":len(spot_in_window),
      "raw_underlying_price_date_coverage_pct":100*len(spot_in_window)/expected_n if expected_n else None,
      "expected_dates_missing_raw_underlying_price":sorted(expected_set-spot_dates),
      "dates_with_qqq_option_rows":len(chain_in_window),
      "option_date_coverage_pct":100*len(chain_in_window)/expected_n if expected_n else None,
      "dates_with_raw_target_pairs":len(pairs_in_window),
      "raw_target_pair_coverage_pct_of_expected_dates":100*len(pairs_in_window)/expected_n if expected_n else None,
      "raw_target_pair_coverage_pct_of_option_dates":100*len(pairs_in_window)/len(chain_in_window) if chain_in_window else None,
      "expected_dates_missing_option_rows":sorted(expected_set-chain_days),
      "expected_dates_with_chain_but_no_valid_pair":sorted(chain_in_window-pairs_in_window),
      "option_dates_outside_universe_window":sorted(chain_days-expected_set),
      "source_date_bounds":{
        "first_raw_underlying_price_date":min(spot_dates) if spot_dates else None,
        "last_raw_underlying_price_date":last_spot,
        "first_qqq_option_chain_date":min(chain_in_window) if chain_in_window else None,
        "last_qqq_option_chain_date":last_chain,
        "expected_sessions_after_last_raw_underlying_price":dates_after_spot,
        "expected_sessions_after_last_qqq_option_chain":dates_after_chain,
        "source_window_complete_through_last_expected_session":bool(
          expected_last and last_spot and last_chain and last_spot>=expected_last and last_chain>=expected_last),
        "calendar_days_from_last_underlying_to_requested_end":
          (date.fromisoformat(end_date)-date.fromisoformat(last_spot)).days if last_spot else None,
        "calendar_days_from_last_option_chain_to_requested_end":
          (date.fromisoformat(end_date)-date.fromisoformat(last_chain)).days if last_chain else None,
      },
    }

def assert_date_ordered_parquet(parquet,path):
    names=list(parquet.schema_arrow.names)
    if "date" not in names:raise ValueError(f"{path.name} missing date")
    date_index=names.index("date")
    last_max=None
    for index in range(parquet.metadata.num_row_groups):
        stats=parquet.metadata.row_group(index).column(date_index).statistics
        if not stats or not stats.has_min_max:
            raise ValueError(f"{path.name} row group {index} lacks date min/max statistics; refusing unsafe streaming grouping")
        mn,mx=day_string(stats.min),day_string(stats.max)
        if not mn or not mx or mn>mx:raise ValueError(f"{path.name} invalid row-group date statistics")
        if last_max is not None and mn<last_max:
            raise ValueError(f"{path.name} row groups are not monotone by date; refusing unsafe streaming grouping")
        last_max=mx

def build_inputs(cache):
    integrity={"files":{}}
    universe_bytes=UNIVERSE_PATH.read_bytes()
    model_bytes=MODEL_SOURCE_PATH.read_bytes()
    helper_bytes=HELPER_SOURCE_PATH.read_bytes()
    sources={
      "src/data/universe.json":(universe_bytes,UNIVERSE_GIT_BLOB_SHA),
      str(MODEL_SOURCE_PATH):(model_bytes,MODEL_SOURCE_GIT_BLOB_SHA),
      str(HELPER_SOURCE_PATH):(helper_bytes,HELPER_SOURCE_GIT_BLOB_SHA),
    }
    for name,(payload,expected) in sources.items():
        actual=git_blob_sha_bytes(payload)
        integrity.setdefault("repo_sources",{})[name]={"bytes":len(payload),"git_blob_sha":actual,"expected":expected,"status":"HASH_VERIFIED" if actual==expected else "HASH_MISMATCH"}
        if actual!=expected:raise ValueError(f"Repo source hash mismatch for {name}; refusing analysis.")
    universe=json.loads(universe_bytes.decode("utf-8"))
    dates=universe.get("dates") or []
    series=universe.get("c") or {}
    qqq=series.get("QQQ") or series.get("qqq")
    vix=series.get("VIX") or series.get("vix")
    if qqq is None or vix is None or len(dates)!=len(qqq) or len(dates)!=len(vix):raise ValueError("Universe arrays missing or misaligned")
    universe_by_day={str(d)[:10]:{"repo_qqq_input":num(q),"vix":num(v)} for d,q,v in zip(dates,qqq,vix)}
    underlying_path,meta=download_verified(UNDERLYING_SPEC,cache)
    integrity["files"][UNDERLYING_SPEC["name"]]=meta
    table=pq.read_table(underlying_path,columns=["date","symbol","close","adjusted_close","volume","split_coefficient"])
    spots={}
    for row in table.to_pylist():
        if str(row.get("symbol","")).upper()!="QQQ":continue
        day=day_string(row.get("date"))
        if START_DATE<=day<=END_DATE:
            spots[day]={"raw_close":num(row.get("close")),"adjusted_close":num(row.get("adjusted_close")),"volume":num(row.get("volume")),"split_coefficient":num(row.get("split_coefficient"))}
    expected=sorted(d for d,values in universe_by_day.items() if START_DATE<=d<=END_DATE and values["repo_qqq_input"] is not None and values["vix"] is not None)
    return integrity,universe_by_day,spots,expected

def finalize_day(day,rows,universe_by_day,spots):
    if not START_DATE<=day<=END_DATE:return None
    universe=universe_by_day.get(day);spot=spots.get(day)
    if not universe or not spot or universe.get("repo_qqq_input") is None or universe.get("vix") is None or spot.get("raw_close") is None:
        return {"date":day,"year":int(day[:4]),"status":"MISSING_RAW_SPOT_OR_UNIVERSE","option_rows":len(rows),"vix_bucket":"UNKNOWN"}
    repo_spot,raw_close,vix=universe["repo_qqq_input"],spot["raw_close"],universe["vix"]
    quote_stats=base.inspect_day(day,rows)
    raw_geom=base.model_qqq_quote(raw_close,vix)
    adj_geom=base.model_qqq_quote(repo_spot,vix)
    match=base.nearest_quote_model_pairs(rows,day,{"raw_close_spot":raw_geom,"repo_adjusted_spot":adj_geom},raw_close,repo_spot,vix)
    pairs=match.get("model_target_nearest_pairs") or {}
    return {
      "date":day,"year":int(day[:4]),"status":match.get("status","NO_PAIR"),"vix":vix,"vix_bucket":vix_bucket(vix),
      "repo_qqq_input":repo_spot,"raw_qqq_close":raw_close,"public_adjusted_close":spot.get("adjusted_close"),
      "repo_spot_vs_raw_close_pct":100*(repo_spot/raw_close-1) if raw_close else None,
      "split_coefficient":spot.get("split_coefficient"),"option_rows":quote_stats.get("row_count",len(rows)),
      "valid_two_sided_quote_pct":quote_stats.get("valid_two_sided_quote_pct"),"call_rows":quote_stats.get("call_rows"),
      "put_rows":quote_stats.get("put_rows"),"candidate_calls_30_60_dte_abs_delta_003_010":quote_stats.get("call_candidates_30_60_dte_abs_delta_0p03_0p10"),
      "selected_expiry":match.get("selected_expiry"),"selected_dte":match.get("calendar_dte"),
      "eligible_rows_in_expiry":match.get("eligible_standard_grid_call_rows_in_expiry"),
      "raw_target_geometry":{"short":raw_geom["short_target_strike"],"wing":raw_geom["long_target_strike"]},
      "adjusted_target_geometry":{"short":adj_geom["short_target_strike"],"wing":adj_geom["long_target_strike"]},
      "raw_target_pair":pair_metrics(pairs.get("raw_close_spot"),vix),
      "adjusted_target_pair":pair_metrics(pairs.get("repo_adjusted_spot"),vix),
    }

def stream_one_file(path,universe_by_day,spots):
    parquet=pq.ParquetFile(path)
    assert_date_ordered_parquet(parquet,path)
    names=set(parquet.schema_arrow.names)
    required=set(OPTION_COLUMNS)
    missing=sorted(required-names)
    if missing:raise ValueError(f"{path.name} missing columns: {missing}")
    daily=[]
    current_day=None
    current_rows=[]
    file_rows=0
    qqq_rows=0
    def flush():
        nonlocal current_day,current_rows
        if current_day is not None:
            result=finalize_day(current_day,current_rows,universe_by_day,spots)
            if result is not None:daily.append(result)
        current_day=None
        current_rows=[]
    for batch in parquet.iter_batches(batch_size=65536,columns=OPTION_COLUMNS):
        for row in batch.to_pylist():
            if str(row.get("symbol","")).upper()!="QQQ":continue
            day=day_string(row.get("date"))
            if not day:continue
            if current_day is None:current_day=day
            elif day!=current_day:
                if day<current_day:raise ValueError(f"{path.name} option rows not sorted by date")
                flush()
                current_day=day
            if START_DATE<=day<=END_DATE:
                current_rows.append(row);file_rows+=1
    flush()
    qqq_rows=file_rows
    return {"file":path.name,"qqq_option_rows_in_window":qqq_rows,"chain_dates":sum(1 for r in daily if r.get("option_rows",0)>0),"paired_dates":sum(1 for r in daily if r.get("raw_target_pair"))},daily

def aggregate(rows):
    matched=[r for r in rows if r.get("raw_target_pair")]
    def vals(key):
        return [r["raw_target_pair"].get(key) for r in matched if r["raw_target_pair"].get(key) is not None]
    gaps=vals("proxy_model_credit_gap_vs_observed")
    ivgaps=vals("chain_iv_model_credit_gap_vs_observed")
    return {
      "days_with_chain_rows":len(rows),"days_with_raw_target_pair":len(matched),
      "pair_coverage_pct":100*len(matched)/len(rows) if rows else None,
      "valid_two_sided_quote_pct_median":summarize_numbers([r.get("valid_two_sided_quote_pct") for r in rows]),
      "repo_spot_vs_raw_close_pct":summarize_numbers([r.get("repo_spot_vs_raw_close_pct") for r in rows]),
      "proxy_credit_gap":summarize_numbers(gaps),"proxy_credit_gap_abs":summarize_numbers([abs(x) for x in gaps]),
      "chain_iv_credit_gap":summarize_numbers(ivgaps),"chain_iv_credit_gap_abs":summarize_numbers([abs(x) for x in ivgaps]),
      "short_delta_abs_error_vs_0p16":summarize_numbers([abs(r["raw_target_pair"]["short_delta"]-.16) for r in matched if r["raw_target_pair"].get("short_delta") is not None]),
      "wing_delta_abs_error_vs_0p08":summarize_numbers([abs(r["raw_target_pair"]["wing_delta"]-.08) for r in matched if r["raw_target_pair"].get("wing_delta") is not None]),
      "proxy_source_iv_ratio_short":summarize_numbers(vals("proxy_to_source_iv_ratio_short")),
      "proxy_source_iv_ratio_wing":summarize_numbers(vals("proxy_to_source_iv_ratio_wing")),
      "fraction_model_haircut_too_narrow_short":sum(1 for r in matched if r["raw_target_pair"].get("model_haircut_narrower_than_observed_short"))/len(matched) if matched else None,
      "fraction_model_haircut_too_narrow_wing":sum(1 for r in matched if r["raw_target_pair"].get("model_haircut_narrower_than_observed_wing"))/len(matched) if matched else None,
    }


def summarize_basis_comparison(daily):
    """Compare target-pair selection using raw nominal spot vs the repo/universe spot input."""
    raw_days=[r for r in daily if r.get("raw_target_pair")]
    repo_days=[r for r in daily if r.get("adjusted_target_pair")]
    matched=[r for r in daily if r.get("raw_target_pair") and r.get("adjusted_target_pair")]

    def pair_values(pair_key, field):
        return [num(r[pair_key].get(field)) for r in matched
                if r.get(pair_key) and num(r[pair_key].get(field)) is not None]

    def abs_delta_error(pair_key, field, target):
        return summarize_numbers([abs(v-target) for v in pair_values(pair_key, field)])

    def geometry_shift(field):
        values=[]
        for r in matched:
            raw_geom=r.get("raw_target_geometry") or {}
            repo_geom=r.get("adjusted_target_geometry") or {}
            raw_strike,repo_strike=num(raw_geom.get(field)),num(repo_geom.get(field))
            if raw_strike is not None and repo_strike is not None and raw_strike>0:
                values.append(100*(repo_strike/raw_strike-1))
        return summarize_numbers(values)

    def fraction(condition):
        return sum(1 for r in matched if condition(r))/len(matched) if matched else None

    return {
      "raw_target_pair_days":len(raw_days),
      "repo_input_target_pair_days":len(repo_days),
      "days_with_both_target_pairs":len(matched),
      "raw_spot_target_pair_delta_error":{
        "short_abs_error_vs_0p16":abs_delta_error("raw_target_pair","short_delta",0.16),
        "wing_abs_error_vs_0p08":abs_delta_error("raw_target_pair","wing_delta",0.08),
      },
      "repo_input_target_pair_delta_error":{
        "short_abs_error_vs_0p16":abs_delta_error("adjusted_target_pair","short_delta",0.16),
        "wing_abs_error_vs_0p08":abs_delta_error("adjusted_target_pair","wing_delta",0.08),
      },
      "repo_input_selected_pair_delta":{
        "short_delta":summarize_numbers(pair_values("adjusted_target_pair","short_delta")),
        "wing_delta":summarize_numbers(pair_values("adjusted_target_pair","wing_delta")),
      },
      "repo_input_geometry_shift_pct_vs_raw_target":{
        "short_target_strike":geometry_shift("short"),
        "wing_target_strike":geometry_shift("wing"),
      },
      "fraction_repo_input_short_delta_gt_0p16":fraction(
        lambda r:num(r["adjusted_target_pair"].get("short_delta")) is not None and num(r["adjusted_target_pair"].get("short_delta"))>0.16),
      "fraction_repo_input_wing_delta_gt_0p08":fraction(
        lambda r:num(r["adjusted_target_pair"].get("wing_delta")) is not None and num(r["adjusted_target_pair"].get("wing_delta"))>0.08),
      "fraction_selected_short_contract_differs":fraction(
        lambda r:r["raw_target_pair"].get("short_contract_id")!=r["adjusted_target_pair"].get("short_contract_id")),
      "fraction_selected_wing_contract_differs":fraction(
        lambda r:r["raw_target_pair"].get("wing_contract_id")!=r["adjusted_target_pair"].get("wing_contract_id")),
      "interpretation":"The two target pairs can select different contracts. This measures target-geometry/selection sensitivity to spot basis; it is not a paired repricing of the same contracts and not a strategy-return test."
    }



ADVERSE_FILL_SLIPPAGE_PER_LEG_USD = (0.0, 0.01, 0.025, 0.05, 0.10)


def summarize_adverse_fill_sensitivity(daily):
    """Stress EOD short-Bid/wing-Ask credit by extra adverse slippage on each leg.

    Per-leg slippage is a scenario input, not observed execution cost. A credit vertical
    loses x on the short leg and x on the long wing, so net credit falls by 2*x/share.
    This reports quote-credit sensitivity only; it is not a fill or strategy-P&L replay.
    """
    rows=[]
    for day in daily:
        pair=day.get("raw_target_pair") or {}
        observed=num(pair.get("observed_executable_side_credit"))
        proxy=num(pair.get("proxy_model_credit_raw_spot"))
        if observed is not None and proxy is not None:
            rows.append({
                "observed_side_credit":observed,
                "proxy_model_credit":proxy,
                "source_iv_model_credit":num(pair.get("chain_iv_model_credit_raw_spot")),
            })
    scenarios=[]
    for per_leg in ADVERSE_FILL_SLIPPAGE_PER_LEG_USD:
        extra_two_leg=2*per_leg
        stressed=[r["observed_side_credit"]-extra_two_leg for r in rows]
        proxy_gap=[r["proxy_model_credit"]-credit for r,credit in zip(rows,stressed)]
        source_iv_gap=[r["source_iv_model_credit"]-credit
                       for r,credit in zip(rows,stressed)
                       if r["source_iv_model_credit"] is not None]
        scenarios.append({
            "extra_adverse_slippage_per_leg_usd":per_leg,
            "extra_two_leg_cost_per_share_usd":extra_two_leg,
            "pairs":len(rows),
            "observed_side_credit_after_slippage":summarize_numbers(stressed),
            "fraction_credit_nonpositive":sum(1 for x in stressed if x<=0)/len(stressed) if stressed else None,
            "proxy_model_minus_stressed_side_credit":summarize_numbers(proxy_gap),
            "source_iv_model_minus_stressed_side_credit":summarize_numbers(source_iv_gap),
        })
    return {
        "definition":"Subtract 2 × per-leg scenario slippage from observed EOD short Bid − wing Ask. Slippage amounts are analyst-selected sensitivities, not measured fills or fees.",
        "not_a_fill_or_strategy_backtest":True,
        "pairs":len(rows),
        "scenarios":scenarios,
    }

def main():
    CACHE_DIR.mkdir(parents=True,exist_ok=True)
    report={
      "research_id":"QQQ_FULL_HISTORY_OPTION_QUOTE_ALIGNMENT_AUDIT_V1",
      "status":"SOURCE_COVERAGE_DIAGNOSTIC","window":{"start":START_DATE,"end":END_DATE},
      "source":"anahatsingh-ui/options-dataset-hist QQQ EOD preservation mirror",
      "quote_time_caveat":"Repository README reports 4:00 PM US Eastern snapshot; this does not establish a fill at the model's decision timestamp.",
      "not_a_strategy_backtest":True,"trade_replay_approved":False,"file_integrity":{},
      "model_source_integrity":{},"annual_file_stats":[],"daily_results":[],"annual_summary":{},"vix_regime_summary":{},"coverage":{},"basis_comparison":{},
    }
    integrity,universe_by_day,spots,expected=build_inputs(CACHE_DIR)
    report["file_integrity"].update(integrity["files"])
    report["model_source_integrity"]=integrity["repo_sources"]
    daily=[]
    for spec in ANNUAL_FILES:
        path,meta=download_verified({"name":spec["name"],"bytes":spec["bytes"],"sha":spec["sha"]},CACHE_DIR)
        report["file_integrity"][spec["name"]]=meta
        stats,rows=stream_one_file(path,universe_by_day,spots)
        report["annual_file_stats"].append(stats)
        daily.extend(rows)
    daily.sort(key=lambda r:r["date"])
    report["daily_results"]=daily
    report["coverage"]=build_coverage_summary(expected,spots,daily,START_DATE,END_DATE)
    report["annual_summary"]={str(year):aggregate([r for r in daily if r["year"]==year and r.get("option_rows",0)>0]) for year in range(2018,2026)}
    buckets=sorted({r.get("vix_bucket","UNKNOWN") for r in daily})
    report["vix_regime_summary"]={bucket:aggregate([r for r in daily if r.get("vix_bucket")==bucket and r.get("option_rows",0)>0]) for bucket in buckets}
    report["overall_alignment"]=aggregate([r for r in daily if r.get("option_rows",0)>0])
    report["basis_comparison"]=summarize_basis_comparison(daily)
    report["adverse_fill_sensitivity"]=summarize_adverse_fill_sensitivity(daily)
    integrity_ok=all(x.get("status") in ("CACHED_HASH_VERIFIED","DOWNLOADED_HASH_VERIFIED") for x in report["file_integrity"].values())
    source_ok=all(x.get("status")=="HASH_VERIFIED" for x in report["model_source_integrity"].values())
    report["integrity_ok"]=integrity_ok and source_ok
    report["overall"]="HASH_VERIFIED_SOURCE_COVERAGE_DIAGNOSTIC" if report["integrity_ok"] else "INTEGRITY_OR_SOURCE_MISMATCH"
    report["limitations"]=[
      "QQQ chain is a public EOD preservation mirror, not exchange-hosted data.",
      "Source-reported IV may be derived from the same quote midpoint and is not independent validation.",
      "EOD snapshots do not prove executable entry/exit at the strategy decision timestamp.",
      "This report contains no portfolio-return or strategy-P&L claim.",
      "VXX option history is not supplied; existing VXX option marks remain DERIVED_BS_VIX / NOT_OPRA.",
    ]
    if not report["coverage"]["source_date_bounds"]["source_window_complete_through_last_expected_session"]:
        cov=report["coverage"]
        end_dates=cov["source_date_bounds"]["expected_sessions_after_last_qqq_option_chain"]
        report["limitations"].append(
          f"Requested window ends {END_DATE}, but raw underlying prices end on "
          f"{cov['source_date_bounds']['last_raw_underlying_price_date']} and QQQ option rows end on "
          f"{cov['source_date_bounds']['last_qqq_option_chain_date']}; "
          f"{len(end_dates)} expected repo-universe sessions remain uncovered after the last option date. "
          "The date denominator is the full repo-universe session index, so missing tail dates are not excluded."
        )
    print("QQQ_FULL_HISTORY_AUDIT_BEGIN")
    print(json.dumps(report,indent=1,sort_keys=True))
    print("QQQ_FULL_HISTORY_AUDIT_END")
    return 0 if report["integrity_ok"] else 1

if __name__=="__main__":raise SystemExit(main())
