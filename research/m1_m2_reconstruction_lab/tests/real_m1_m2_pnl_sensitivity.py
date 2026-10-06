#!/usr/bin/env python3
"""REAL M1/M2 vs archive proxy controlled Original-Hybrid P&L replay.

Scope lock:
- 2018-03-01 through 2022-04-08 only, where observed M1/M2 overlap exists.
- Same QQQ/VXX/VIX spot fixture.
- Same derived BS/VIX option pricing and execution as the frozen source-logic replay.
- ONLY term-slope input changes:
    PROXY = 0.10*tanh((VIX_MA20-VIX)/6)
    REAL  = (M2-M1)/M1
- No parameter search.
- This is a controlled derived P&L sensitivity, NOT a re-certification of 12.7049%.
"""
import argparse, json, math, hashlib
from pathlib import Path
import numpy as np, pandas as pd
from math import erf, sqrt, exp, log
from scipy.stats import norm

CAPITAL=100000.0
BASE_QCC_RISK=0.008
BASE_RV=0.02
R_RATE=.03
Q_QQQ=.004

def N(x): return .5*(1+erf(x/sqrt(2)))
def d1d2(S,K,T,r,sig,q=0):
    vs=sig*sqrt(max(T,1e-8))
    d1=(log(S/K)+(r-q+.5*sig*sig)*T)/vs
    return d1,d1-vs
def bsCall(S,K,T,r,sig,q=0):
    if T<=1/365 or sig<1e-8: return max(S-K,0)
    d1,d2=d1d2(S,K,T,r,sig,q)
    return S*exp(-q*T)*N(d1)-K*exp(-r*T)*N(d2)
def bsDelta(S,K,T,r,sig,q=0):
    if T<=1/365 or sig<1e-8: return 1.0 if S>K else 0.0
    d1,_=d1d2(S,K,T,r,sig,q)
    return exp(-q*T)*N(d1)
def strikeFromCallDelta(S,T,r,q,sig,target):
    p=min(max(target*exp(q*T),1e-6),1-1e-6)
    d1=norm.ppf(p); vs=sig*sqrt(T)
    return max(S*exp(-(d1*vs-(r-q+.5*sig*sig)*T)),1e-6)
def ivVxx(vix): return min(max(.48+1.35*(vix/100),.42),1.8)
def ivQqq(vix): return min(max(1.08*(vix/100),.1),.9)
def halfSpreadV(vix): return min(max(.035+.14*max(vix/100-.16,0),.03),.16)
def halfSpreadQ(vix): return min(max(.025+.08*max(vix/100-.16,0),.02),.1)
def ivVxxCall(vix): return min(ivVxx(vix)*1.12,2.2)
def quoteCC(S,vix,T,kind,half):
    if kind=='vxx':
        sigS=ivVxxCall(vix); sigL=sigS*.96; q=0
    else:
        sigS=ivQqq(vix)*.95; sigL=ivQqq(vix)*.9; q=Q_QQQ
    Ks=strikeFromCallDelta(S,T,R_RATE,q,sigS,.35 if kind=='vxx' else .16)
    Kl=strikeFromCallDelta(S,T,R_RATE,q,sigL,.16 if kind=='vxx' else .08)
    if Kl<=Ks: Kl=Ks*(1.14 if kind=='vxx' else 1.06)
    midS=bsCall(S,Ks,T,R_RATE,sigS,q); midL=bsCall(S,Kl,T,R_RATE,sigL,q)
    credit=max(midS*(1-half)-midL*(1+half),1e-4)
    return {'Ks':Ks,'Kl':Kl,'premium':credit,'width':Kl-Ks}

def simulate(df, mode):
    x=df.copy().sort_values('date').reset_index(drop=True)
    x['rQ']=x.qqq.pct_change().fillna(0); x['rV']=x.vxx.pct_change().fillna(0)
    x['vixma']=x.vix.rolling(20,min_periods=1).mean()
    if mode=='REAL':
        x['ts']=(x.m2-x.m1)/x.m1
    else:
        x['ts']=.10*np.tanh((x.vixma-x.vix)/6.0)
    cash=CAPITAL; legs=[]; eq=[]; opens=[]; closes=[]; peak=CAPITAL
    for i,row in x.iterrows():
        keep=[]
        for p in legs:
            dte=max(p['expiry_i']-i,0)
            if p['structure']=='qqq-long':
                keep.append(p); continue
            if p['structure']=='vxx-short':
                pnl=(p['S0']-row.vxx)*p['n']; liq=-row.vxx*p['n']
                fire=(row.rV>.06 or row.vix>35 or row.ts<0 or dte<=7 or
                      pnl/(p['S0']*p['n'])<=-.5)
                if fire:
                    cash+=liq; closes.append((row.date,'vxx-short',p['n'],pnl))
                else: keep.append(p)
                continue
            kind=p['kind']; S=row.vxx if kind=='vxx' else row.qqq
            half=halfSpreadV(row.vix) if kind=='vxx' else halfSpreadQ(row.vix)
            qvol=0 if kind=='vxx' else Q_QQQ
            sigS=ivVxxCall(row.vix) if kind=='vxx' else ivQqq(row.vix)*.95
            sigL=sigS*.96 if kind=='vxx' else ivQqq(row.vix)*.9
            T=max(dte/365,1/365)
            exitp=bsCall(S,p['Ks'],T,R_RATE,sigS,qvol)*(1+half)-bsCall(S,p['Kl'],T,R_RATE,sigL,qvol)*(1-half)
            pnl=(p['premium']-exitp)*100*p['n']; liq=-exitp*100*p['n']
            risk=(p['width']-p['premium'])*100*p['n']
            fire=(dte<=7 or pnl/risk<=-.55 or pnl/risk>=.5)
            if fire:
                cash+=liq; closes.append((row.date,p['structure'],p['n'],pnl))
            else: keep.append(p)
        legs=keep
        def liq():
            v=0
            for p in legs:
                dte=max(p['expiry_i']-i,0)
                if p['structure']=='qqq-long': v+=row.qqq*p['n']
                elif p['structure']=='vxx-short': v-=row.vxx*p['n']
                else:
                    kind=p['kind']; S=row.vxx if kind=='vxx' else row.qqq
                    half=halfSpreadV(row.vix) if kind=='vxx' else halfSpreadQ(row.vix)
                    qvol=0 if kind=='vxx' else Q_QQQ
                    sigS=ivVxxCall(row.vix) if kind=='vxx' else ivQqq(row.vix)*.95
                    sigL=sigS*.96 if kind=='vxx' else ivQqq(row.vix)*.9
                    T=max(dte/365,1/365)
                    ep=bsCall(S,p['Ks'],T,R_RATE,sigS,qvol)*(1+half)-bsCall(S,p['Kl'],T,R_RATE,sigL,qvol)*(1-half)
                    v-=ep*100*p['n']
            return v
        nav=cash+liq(); peak=max(peak,nav)
        state='Shock' if (row.rV>.06 or row.vix>35 or row.rQ<-.03) else ('High-Spread' if halfSpreadV(row.vix)>.14 else ('Decay-Optimal' if row.ts>=0 and row.vix<28 else 'Normal'))
        wantV=state!='Shock' and row.ts>=0
        structs={p['structure'] for p in legs}
        def open_leg(st,frac):
            nonlocal cash
            if st in structs or frac<=0:return
            if st=='qqq-long':
                n=math.floor(nav*frac/row.qqq)
                if n: cash-=row.qqq*n; legs.append({'structure':st,'n':n,'S0':row.qqq,'expiry_i':i+100000}); opens.append((row.date,st,n))
            elif st=='vxx-short':
                n=math.floor(nav*frac/row.vxx)
                if n: cash+=row.vxx*n; legs.append({'structure':st,'n':n,'S0':row.vxx,'expiry_i':i+21}); opens.append((row.date,st,n))
            else:
                kind='vxx' if st=='vxx-cc' else 'qqq'
                half=halfSpreadV(row.vix) if kind=='vxx' else halfSpreadQ(row.vix)
                q=quoteCC(row.vxx if kind=='vxx' else row.qqq,row.vix,30/365,kind,half)
                frac_use=BASE_RV if kind=='vxx' else BASE_QCC_RISK
                n=math.floor(nav*frac_use/((q['width']-q['premium'])*100))
                if n:
                    cash+=q['premium']*100*n
                    legs.append({'structure':st,'kind':kind,'n':n,'S0':row.vxx if kind=='vxx' else row.qqq,
                                 'Ks':q['Ks'],'Kl':q['Kl'],'premium':q['premium'],'width':q['width'],'expiry_i':i+21})
                    opens.append((row.date,st,n))
        open_leg('qqq-long',.42)
        open_leg('qqq-cc',.008)
        if wantV:
            open_leg('vxx-short',.18); open_leg('vxx-cc',.02)
        nav=cash+liq(); eq.append((row.date,nav))
    e=pd.DataFrame(eq,columns=['date','nav'])
    e['peak']=e.nav.cummax(); e['dd']=e.nav/e.peak-1
    years=(e.date.iloc[-1]-e.date.iloc[0]).days/365.25
    cagr=(e.nav.iloc[-1]/CAPITAL)**(1/years)-1
    return {'mode':mode,'cagr':float(cagr),'maxdd':float(e.dd.min()),'final_nav':float(e.nav.iloc[-1]),
            'opens':len(opens),'closes':len(closes),'equity':e}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--spots',required=True)
    ap.add_argument('--m1m2',required=True)
    ap.add_argument('--out',default='artifacts/real-m1m2-pnl')
    a=ap.parse_args(); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    s=pd.read_csv(a.spots); s['Date']=pd.to_datetime(s['Date']).dt.date
    s=s.rename(columns={'Date':'date','QQQ':'qqq','VXX':'vxx','VIX':'vix'})
    m=pd.read_csv(a.m1m2); m['Date']=pd.to_datetime(m['Date']).dt.date
    m=m.rename(columns={'Date':'date','M1':'m1','M2':'m2'})
    d=s.merge(m[['date','M1','M2']],on='date',how='inner')
    d=d[(d.date>=pd.to_datetime('2018-03-01').date())&(d.date<=pd.to_datetime('2022-04-08').date())].dropna()
    d=d.sort_values('date').reset_index(drop=True)
    if len(d)<1000: raise SystemExit(f'Unexpected overlap rows: {len(d)}')
    results=[]
    for mode in ('PROXY','REAL'):
        r=simulate(d,mode); r['equity'].to_csv(out/f'{mode.lower()}_equity.csv',index=False)
        results.append({k:v for k,v in r.items() if k!='equity'})
    delta={k:results[1][k]-results[0][k] for k in ('cagr','maxdd','final_nav','opens','closes')}
    report={'status':'CONTROLLED_DERIVED_PNL_SENSITIVITY','window':[str(d.date.min()),str(d.date.max())],
            'rows':len(d),'real_m1m2_rows':len(m),'contract':'same spot/BS/VIX/execution; only term slope changed',
            'proxy':'0.10*tanh((VIX_MA20-VIX)/6)','real':'(M2-M1)/M1',
            'results':results,'delta_REAL_minus_PROXY':delta,
            'reference_12_7049_percent_cagr':'REFERENCE_ONLY_NOT_REPLAYED',
            'full_2018_2026_real_m1m2':'BLOCKED — observed M1/M2 coverage ends 2022-04-08'}
    (out/'report.json').write_text(json.dumps(report,indent=2,default=str),encoding='utf-8')
    print(json.dumps(report,indent=2,default=str))
if __name__=='__main__': main()
