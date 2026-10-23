#!/usr/bin/env python3
"""Validate the frozen prospective protocol and gate source data readiness."""
from __future__ import annotations
import argparse, csv, hashlib, json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_PROTOCOL = HERE / "prospective_oos_protocol_v1.json"
DEFAULT_DATA_DIR = HERE / "data" / "prospective_oos"
REQUIRED_OPTIONS = {"date","contract_id","symbol","expiration","strike","type","bid","ask","bid_size","ask_size","delta"}
REQUIRED_SPOTS = {"date","symbol","close"}

def validate_protocol(protocol):
    problems=[]
    if protocol.get("historical_cutoff") != "2025-12-15": problems.append("historical cutoff must remain frozen at 2025-12-15")
    if protocol.get("primary_candidate") != {"ratio":"1:3","exit_policy":"HOLD_20_SESSIONS","interpretation":"provisional candidate only; historical advantage is in-sample and not evidence of forward alpha"}:
        problems.append("primary candidate or exit policy changed")
    if protocol.get("quantities",{}).get("ratios_in_scope") != ["1:3","2:4","4:5","1:6"]:
        problems.append("locked ratio list changed")
    if protocol.get("entry",{}).get("signal") != "QQQ trailing 20-common-session close-to-close return is below SPY trailing 20-common-session return":
        problems.append("entry signal changed")
    if protocol.get("entry",{}).get("cohort_stride_common_sessions") != 45: problems.append("cohort stride changed")
    if protocol.get("contracts",{}).get("same_expiration_required") is not True: problems.append("same-expiry control changed")
    if protocol.get("contracts",{}).get("dte_min") != 30 or protocol.get("contracts",{}).get("dte_max") != 60 or protocol.get("contracts",{}).get("dte_target") != 45:
        problems.append("DTE controls changed")
    if protocol.get("contracts",{}).get("absolute_delta_target") != 0.25: problems.append("delta target changed")
    if protocol.get("contracts",{}).get("allow_contract_substitution") is not False: problems.append("contract substitution must remain disabled")
    if protocol.get("contracts",{}).get("allow_forward_fill") is not False: problems.append("forward filling must remain disabled")
    if protocol.get("quote_depth",{}).get("required") is not True: problems.append("quote depth gate must remain enabled")
    if protocol.get("reporting",{}).get("unresolved_assigned_zero_pnl") is not False: problems.append("unresolved trades cannot be assigned zero P&L")
    if protocol.get("execution_safety",{}).get("paper_replay_only") is not True or protocol.get("execution_safety",{}).get("live_orders") is not False:
        problems.append("execution safety controls changed")
    if protocol.get("source_gate",{}).get("price_only_data_can_be_primary") is not False: problems.append("price-only data must not become the primary evidence")
    return problems

def sha256_file(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""): h.update(block)
    return h.hexdigest()

def validate_csv(path, required_columns, date_column="date"):
    errors=[]
    if not path.is_file(): return [f"missing required file: {path.name}"]
    with path.open("r",encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        fields=set(reader.fieldnames or [])
        missing=required_columns-fields
        if missing: return [f"{path.name} missing columns: {sorted(missing)}"]
        rows=0
        min_date=max_date=None
        for row in reader:
            rows+=1
            day=(row.get(date_column) or "").strip()[:10]
            if not day: errors.append(f"{path.name} row {rows+1} has empty {date_column}"); continue
            min_date=day if min_date is None or day<min_date else min_date
            max_date=day if max_date is None or day>max_date else max_date
            if date_column=="date" and day <= "2025-12-15":
                errors.append(f"{path.name} contains non-prospective date {day}")
                break
            if required_columns is REQUIRED_OPTIONS:
                try:
                    bid=float(row["bid"]); ask=float(row["ask"])
                    bid_size=int(float(row["bid_size"])); ask_size=int(float(row["ask_size"]))
                    delta=float(row["delta"]); strike=float(row["strike"])
                except (TypeError,ValueError):
                    errors.append(f"{path.name} row {rows+1} has nonnumeric quote/size/Greek"); break
                if bid<0 or ask<=0 or bid>ask or bid_size<0 or ask_size<0 or strike<=0:
                    errors.append(f"{path.name} row {rows+1} has invalid quote/size/strike"); break
        if rows==0: errors.append(f"{path.name} has no data rows")
    return errors

def readiness(protocol, data_dir):
    problems=validate_protocol(protocol)
    report={"protocol_id":protocol.get("protocol_id"),"protocol_valid":not problems,
            "protocol_errors":problems,"status":"BLOCKED_MISSING_FRESH_QUOTES",
            "data_dir":str(data_dir),"source_manifest_present":False,"verified_files":[],
            "data_errors":[],"replay_performed":False,
            "note":"Protocol validation is not a performance test. No prospective P&L is reported until fresh source files with quote sizes and source hashes are supplied."}
    manifest_path=data_dir/"source_manifest.json"
    if not manifest_path.is_file():
        report["data_errors"].append("source_manifest.json is absent; require provider, snapshot convention, date range, files and SHA-256 hashes")
        return report
    report["source_manifest_present"]=True
    try: manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as e:
        report["data_errors"].append(f"invalid source manifest: {e}")
        return report
    if not manifest.get("provider") or not manifest.get("snapshot_convention"):
        report["data_errors"].append("manifest must identify provider and snapshot convention")
    files=manifest.get("files")
    if not isinstance(files,list) or not files:
        report["data_errors"].append("manifest files list is empty")
        return report
    for item in files:
        rel=item.get("path","")
        path=(data_dir/rel).resolve()
        if not rel or data_dir.resolve() not in path.parents:
            report["data_errors"].append(f"invalid path in manifest: {rel}"); continue
        if not path.is_file():
            report["data_errors"].append(f"missing input file: {rel}"); continue
        expected=item.get("sha256","")
        actual=sha256_file(path)
        if actual!=expected:
            report["data_errors"].append(f"SHA-256 mismatch: {rel}"); continue
        role=item.get("role")
        if role=="options":
            errs=validate_csv(path,REQUIRED_OPTIONS)
            report["data_errors"].extend(f"{rel}: {e}" for e in errs)
        elif role=="underlying":
            errs=validate_csv(path,REQUIRED_SPOTS)
            report["data_errors"].extend(f"{rel}: {e}" for e in errs)
        else:
            report["data_errors"].append(f"{rel}: role must be options or underlying")
            continue
        report["verified_files"].append({"path":rel,"role":role,"sha256":actual})
    if not problems and not report["data_errors"] and report["verified_files"]:
        report["status"]="READY_FOR_REPLAY"
        report["note"]="Inputs passed manifest, hash and canonical-schema gates. This status means ready for replay only, not profitable or executable."
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--protocol",type=Path,default=DEFAULT_PROTOCOL)
    p.add_argument("--data-dir",type=Path,default=DEFAULT_DATA_DIR)
    p.add_argument("--out",type=Path,default=HERE/"results"/"prospective_oos_readiness.json")
    a=p.parse_args()
    protocol=json.loads(a.protocol.read_text(encoding="utf-8"))
    result=readiness(protocol,a.data_dir)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps({"status":result["status"],"protocol_valid":result["protocol_valid"],
      "source_manifest_present":result["source_manifest_present"],"verified_files":len(result["verified_files"]),
      "data_errors":result["data_errors"],"replay_performed":False},indent=2))
    if result["protocol_errors"]: raise SystemExit(2)

if __name__=="__main__": main()
