#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, itertools, json, math
from math import erf, sqrt, exp, log
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import norm

CAPITAL = 100000.0
BASE_QCC_RISK = 0.008
BASE_RV = 0.02
APPROACH = 0.98

def N(x):
    return 0.5 * (1 + erf(x / sqrt(2)))

def d1d2(S, K, T, r, sig, q=0):
    vs = sig * sqrt(max(T, 1e-8))
    d1 = (log(S / K) + (r - q + 0.5 * sig * sig) * T) / vs
    return d1, d1 - vs

def bsCall(S, K, T, r, sig, q=0):
    if T <= 1 / 365 or sig < 1e-8:
        return max(S - K, 0)
    d1, d2 = d1d2(S, K, T, r, sig, q)
    return S * exp(-q * T) * N(d1) - K * exp(-r * T) * N(d2)

def strikeFromCallDelta(S, T, r, q, sig, target):
    p = min(max(target * exp(q * T), 1e-6), 1 - 1e-6)
    d1 = norm.ppf(p)
    vs = sig * sqrt(T)
    return max(S * exp(-(d1 * vs - (r - q + 0.5 * sig * sig) * T)), 1e-6)

def ivVxx(vix):
    return min(max(.48 + 1.35 * (vix / 100), .42), 1.8)

def ivQqq(vix):
    return min(max(1.08 * (vix / 100), .1), .9)

def halfSpreadV(vix):
    return min(max(.035 + .14 * max(vix / 100 - .16, 0), .03), .16)

def halfSpreadQ(vix):
    return min(max(.025 + .08 * max(vix / 100 - .16, 0), .02), .1)

def ivVxxCall(vix):
    return min(ivVxx(vix) * 1.12, 2.2)

def quoteCC(S, vix, T, kind, half):
    if kind == 'vxx':
        sigS = ivVxxCall(vix)
        sigL = sigS * .96
        q = 0
    else:
        sigS = ivQqq(vix) * .95
        sigL = ivQqq(vix) * .9
        q = .004
    Ks = strikeFromCallDelta(S, T, .03, q, sigS, .35 if kind == 'vxx' else .16)
    Kl = strikeFromCallDelta(S, T, .03, q, sigL, .16 if kind == 'vxx' else .08)
    if Kl <= Ks:
        Kl = Ks * (1.14 if kind == 'vxx' else 1.06)
    midS = bsCall(S, Ks, T, .03, sigS, q)
    midL = bsCall(S, Kl, T, .03, sigL, q)
    credit = max(midS * (1 - half) - midL * (1 + half), 1e-4)
    return {'Ks': Ks, 'Kl': Kl, 'premium': credit, 'width': Kl - Ks}

def portfolio_liq(df, i, legs):
    row = df.iloc[i]
    liq = 0.0
    for p in legs:
        dte = max(p['expiry_i'] - i, 0)
        if p['structure'] == 'qqq-long':
            liq += row.qqq * p['n']
        elif p['structure'] == 'vxx-short':
            liq += -row.vxx * p['n']
        else:
            kind = p['kind']
            S = row.vxx if kind == 'vxx' else row.qqq
            half = halfSpreadV(row.vix) if kind == 'vxx' else halfSpreadQ(row.vix)
            qvol = 0 if kind == 'vxx' else .004
            sigS = ivVxxCall(row.vix) if kind == 'vxx' else ivQqq(row.vix) * .95
            sigL = sigS * .96 if kind == 'vxx' else ivQqq(row.vix) * .9
            T = max(dte / 365, 1 / 365)
            exitp = (
                bsCall(S, p['Ks'], T, .03, sigS, qvol) * (1 + half)
                - bsCall(S, p['Kl'], T, .03, sigL, qvol) * (1 - half)
            )
            liq += -exitp * 100 * p['n']
    return liq

def simulate(spots_path, include):
    data = json.load(open(spots_path, encoding='utf-8'))
    df = pd.DataFrame({
        'date': pd.to_datetime(data['dates']),
        'qqq': data['qqq'],
        'vxx': data['vxx'],
        'vix': data['vix'],
    })
    df['rQ'] = df.qqq.pct_change().fillna(0)
    df['rV'] = df.vxx.pct_change().fillna(0)
    df['vixma'] = df.vix.rolling(20).mean()
    df['ts'] = np.tanh((df.vixma - df.vix) / 6) * .1
    df['r5'] = df.qqq.pct_change(5).fillna(0)
    df['r10'] = df.qqq.pct_change(10).fillna(0)
    df['high52'] = df.qqq.rolling(252, min_periods=1).max()

    cash = CAPITAL
    legs = []
    eq = []
    peak = CAPITAL
    events = []
    opens = []
    closes = []

    for i, row in df.iterrows():
        keep = []
        for p in legs:
            dte = max(p['expiry_i'] - i, 0)
            if p['structure'] == 'qqq-long':
                keep.append(p)
            elif p['structure'] == 'vxx-short':
                pnl = (p['S0'] - row.vxx) * p['n']
                liq = -row.vxx * p['n']
                fire = (
                    row.rV > .06 or row.vix > 35 or row.ts < 0 or
                    dte <= 7 or (pnl / (p['S0'] * p['n']) <= -0.5)
                )
                if fire:
                    cash += liq
                    closes.append((row.date, p['structure'], p['n'], pnl))
                else:
                    keep.append(p)
            else:
                kind = p['kind']
                S = row.vxx if kind == 'vxx' else row.qqq
                half = halfSpreadV(row.vix) if kind == 'vxx' else halfSpreadQ(row.vix)
                qvol = 0 if kind == 'vxx' else .004
                sigS = ivVxxCall(row.vix) if kind == 'vxx' else ivQqq(row.vix) * .95
                sigL = sigS * .96 if kind == 'vxx' else ivQqq(row.vix) * .9
                T = max(dte / 365, 1 / 365)
                exitp = (
                    bsCall(S, p['Ks'], T, .03, sigS, qvol) * (1 + half)
                    - bsCall(S, p['Kl'], T, .03, sigL, qvol) * (1 - half)
                )
                pnl = (p['premium'] - exitp) * 100 * p['n']
                liq = -exitp * 100 * p['n']
                risk = (p['width'] - p['premium']) * 100 * p['n']
                fire = dte <= 7 or (pnl / risk <= -0.55) or (pnl / risk >= .5)
                if fire:
                    cash += liq
                    closes.append((row.date, p['structure'], p['n'], pnl))
                    events.append({
                        'date': str(row.date.date()),
                        'event': 'CLOSE_' + p['structure'].replace('-', '_'),
                        'n': int(p['n']),
                        'pnl': float(pnl),
                    })
                else:
                    keep.append(p)
        legs = keep

        nav = cash + portfolio_liq(df, i, legs)
        peak = max(peak, nav)
        eq.append((row.date, nav))

        def open_leg(st, frac):
            nonlocal cash, legs
            structs = {p['structure'] for p in legs}
            if st in structs or frac <= 0:
                return
            if st == 'qqq-long':
                n = math.floor(nav * frac / row.qqq)
                if n:
                    cash -= row.qqq * n
                    legs.append({'structure': st, 'n': n, 'S0': row.qqq, 'expiry_i': i + 100000})
                    opens.append((row.date, st, n))
            elif st == 'vxx-short':
                n = math.floor(nav * frac / row.vxx)
                if n:
                    cash += row.vxx * n
                    legs.append({'structure': st, 'n': n, 'S0': row.vxx, 'expiry_i': i + 21})
                    opens.append((row.date, st, n))
            else:
                kind = 'vxx' if st == 'vxx-cc' else 'qqq'
                half = halfSpreadV(row.vix) if kind == 'vxx' else halfSpreadQ(row.vix)
                q = quoteCC(row.vxx if kind == 'vxx' else row.qqq, row.vix, 30 / 365, kind, half)
                frac_use = BASE_RV if kind == 'vxx' else BASE_QCC_RISK
                n = math.floor(nav * frac_use / ((q['width'] - q['premium']) * 100))
                if n:
                    cash += q['premium'] * 100 * n
                    legs.append({
                        'structure': st, 'kind': kind, 'n': n,
                        'S0': row.vxx if kind == 'vxx' else row.qqq,
                        'Ks': q['Ks'], 'Kl': q['Kl'],
                        'premium': q['premium'], 'width': q['width'],
                        'expiry_i': i + 21,
                    })
                    opens.append((row.date, st, n))
                    events.append({'date': str(row.date.date()), 'event': 'OPEN_' + st.replace('-', '_'), 'n': int(n)})

        if include['core']:
            open_leg('qqq-long', .42)
        if include['qcc']:
            open_leg('qqq-cc', .008)
        if include['vxx_short'] and row.ts >= 0 and not (row.rV > .06 or row.vix > 35 or row.rQ < -.03):
            open_leg('vxx-short', .18)
        if include['vxx_cc'] and row.ts >= 0 and not (row.rV > .06 or row.vix > 35 or row.rQ < -.03):
            open_leg('vxx-cc', .02)

    e = pd.DataFrame(eq, columns=['date', 'nav'])
    e['peak'] = e.nav.cummax()
    e['dd'] = e.nav / e.peak - 1
    years = max((e.date.iloc[-1] - e.date.iloc[0]).days / 365.25, 1/365.25)
    cagr = (e.nav.iloc[-1] / CAPITAL) ** (1 / years) - 1
    return {
        'cagr': float(cagr),
        'maxdd': float(e.dd.min()),
        'final_nav': float(e.nav.iloc[-1]),
        'years': float(years),
        'opens': len(opens),
        'closes': len(closes),
    }, e

def shapley(values, baseline_key):
    layers = ['core','qcc','vxx_short','vxx_cc']
    full = values[tuple([1]*4)]['final_nav']
    contrib = {k: 0.0 for k in layers}
    for i, layer in enumerate(layers):
        others = [j for j in range(4) if j != i]
        total = 0.0
        for r in range(4):
            for comb in itertools.combinations(others, r):
                mask0 = [0]*4
                for j in comb:
                    mask0[j] = 1
                mask1 = mask0.copy()
                mask1[i] = 1
                v0 = values[tuple(mask0)]['final_nav']
                v1 = values[tuple(mask1)]['final_nav']
                weight = math.factorial(r) * math.factorial(3-r) / math.factorial(4)
                total += weight * (v1 - v0)
        contrib[layer] = total
    return contrib

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--spots-path', required=True)
    ap.add_argument('--out', default='artifacts')
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    layers = ['core','qcc','vxx_short','vxx_cc']
    values = {}
    curves = {}
    for mask in itertools.product([0,1], repeat=4):
        include = dict(zip(layers, map(bool, mask)))
        stats, e = simulate(args.spots_path, include)
        values[mask] = stats
        curves[''.join(map(str, mask))] = e
    full_mask = (1,1,1,1)
    base = values[full_mask]
    rows = []
    for mask, s in sorted(values.items()):
        rows.append({
            'mask': ''.join(map(str, mask)),
            **s,
            'core': bool(mask[0]),
            'qcc': bool(mask[1]),
            'vxx_short': bool(mask[2]),
            'vxx_cc': bool(mask[3]),
        })
    pd.DataFrame(rows).to_csv(out / 'component_ablation.csv', index=False)

    for key,e in curves.items():
        e.to_csv(out / f'equity_mask_{key}.csv', index=False)

    loo = []
    for i, layer in enumerate(layers):
        mask = list(full_mask)
        mask[i] = 0
        mask = tuple(mask)
        s = values[mask]
        loo.append({
            'layer': layer,
            'full_final_nav': base['final_nav'],
            'without_final_nav': s['final_nav'],
            'delta_final_nav': base['final_nav'] - s['final_nav'],
            'full_cagr': base['cagr'],
            'without_cagr': s['cagr'],
            'delta_cagr': base['cagr'] - s['cagr'],
            'full_maxdd': base['maxdd'],
            'without_maxdd': s['maxdd'],
        })
    pd.DataFrame(loo).to_csv(out / 'component_leave_one_out.csv', index=False)

    shap = shapley(values, full_mask)
    pd.DataFrame([{'layer':k,'shapley_delta_final_nav':v} for k,v in shap.items()]).to_csv(out / 'component_shapley_final_nav.csv', index=False)

    report = {
        'research_id': 'QQQ_HYBRID_COMPONENT_DECOMPOSITION_V1',
        'status': 'DERIVED_REPLAY',
        'pricing_model': 'DERIVED_BS_VIX',
        'not_opra': True,
        'data_sha256': sha256_file(args.spots_path),
        'rules': {
            'qqq_core': '42% of NAV',
            'qcc': '0.8% risk budget; 30D derived BS/VIX call credit spread',
            'vxx_short': '18% notional when non-shock state and term proxy nonnegative',
            'vxx_call_spread': '2% risk budget when non-shock state and term proxy nonnegative',
            'vxx_shock_exit': 'rV>6% or VIX>35 or term_slope_proxy<0 or QQQ daily<-3%',
            'no_parameter_search': True,
        },
        'full': base,
        'leave_one_out': loo,
        'shapley_final_nav': shap,
        'note': 'This is a component-ablation study of the source-aligned original hybrid. Shapley is a marginal attribution of terminal NAV under the tested game; it is not a claim that daily P&L components are additive.',
    }
    (out / 'qqq_hybrid_component_decomposition_v1_report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
