#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, math
from math import erf, sqrt, exp, log
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import norm

CAPITAL=100000.0
CORE_FRAC=.42
FAR_DTE=120
NEAR_DTE=30
FAR_DELTA=.08
LONG_DELTA=.50
COVERAGE_MULT=1.50
MAX_STACK=5
RISK_BUDGET=.008
BASE_RV=.02
VXX_SHORT_FRAC=.18
VXX_CC_RISK=.02

def N(x): return .5*(1+erf(x/sqrt(2)))
def d1d2(S,K,T,r,sig,q=0):
    vs=sig*sqrt(max(T,1e-8)); d1=(log(S/K)+(r-q+.5*sig*sig)*T)/vs; return d1,d1-vs
def call(S,K,T,r,sig,q=0):
    if T<=1/365 or sig<1e-8: return max(S-K,0)
    d1,d2=d1d2(S,K,T,r,sig,q)
    return S*exp(-q*T)*N(d1)-K*exp(-r*T)*N(d2)
def delta(S,K,T,r,sig,q=0):
    if T<=1/365 or sig<1e-8: return 1. if S>K else 0.
    d1,_=d1d2(S,K,T,r,sig,q); return exp(-q*T)*N(d1)
def strike_for_delta(S,T,r,q,sig,target):
    p=min(max(target*exp(q*T),1e-6),1-1e-6)
    d1=norm.ppf(p); vs=sig*sqrt(T)
    return max(S*exp(-(d1*vs-(r-q+.5*sig*sig)*T)),1e-6)
def ivq(vix): return min(max(1.08*(vix/100),.10),.90)
def ivv(vix): return min(max(.48+1.35*(vix/100),.42),1.8)
def sprq(vix): return min(max(.025+.08*max(vix/100-.16,0),.02),.10)
def sprv(vix): return min(max(.035+.14*max(vix/100-.16,0),.03),.16)
def ivvc(vix): return min(ivv(vix)*1.12,2.2)

def qqq_far(S,vix,T):
    sig=ivq(vix)*.95
    K=strike_for_delta(S,T,.03,.004,sig,FAR_DELTA)
    bid=call(S,K,T,.03,sig,.004)*(1-sprq(vix))
    ask=call(S,K,T,.03,sig,.004)*(1+sprq(vix))
    return K,bid,ask,sig
def qqq_near(S,vix,T):
    sig=ivq(vix)*.95
    K=strike_for_delta(S,T,.03,.004,sig,LONG_DELTA)
    bid=call(S,K,T,.03,sig,.004)*(1-sprq(vix))
    ask=call(S,K,T,.03,sig,.004)*(1+sprq(vix))
    return K,bid,ask,sig
def vxx_cc(S,vix,T):
    sigs=ivvc(vix); sigl=sigs*.96
    Ks=strike_for_delta(S,T,.03,0,sigs,.35)
    Kl=strike_for_delta(S,T,.03,0,sigl,.16)
    if Kl<=Ks: Kl=Ks*1.14
    ms=call(S,Ks,T,.03,sigs,0); ml=call(S,Kl,T,.03,sigl,0); h=sprv(vix)
    return Ks,Kl,max(ms*(1-h)-ml*(1+h),1e-4)

def max_loss_ratio(S,vix,Ns):
    T=FAR_DTE/365
    Kf,_,_,sigf=qqq_far(S,vix,T)
    Kl,_,_,sigl=qqq_near(S,vix,NEAR_DTE/365)
    # One near ATM long per dynamic target is the basic unit; N far shorts are covered by target_count.
    target=max(1,min(MAX_STACK,math.ceil(COVERAGE_MULT*Ns*FAR_DELTA/LONG_DELTA)))
    grid=np.linspace(max(1,S*.2),max(S*2.5,Kf*1.25),800)
    init=call(S,Kl,NEAR_DTE/365,.03,sigl,.004)-Ns*call(S,Kf,T,.03,sigf,.004)
    payoff=np.maximum(grid-Kl,0)-Ns*np.maximum(grid-Kf,0)
    return max(0.,-float(np.min((payoff-init*100.0*0+0)))),target,Kl,Kf

# The payoff is evaluated directly in dollars per share; the state sizing uses
# the limited-loss proxy of the far-call / near-call package.
def package_entry(S,vix,Ns,nav):
    Tfar=FAR_DTE/365; Tnear=NEAR_DTE/365
    Kf,fbid,fask,sigf=qqq_far(S,vix,Tfar)
    Kn,nbid,nask,sign=qqq_near(S,vix,Tnear)
    target=max(1,min(MAX_STACK,math.ceil(COVERAGE_MULT*Ns*FAR_DELTA/LONG_DELTA)))
    debit=(target*nask-Ns*fbid)*100
    # Hard cash-at-entry guard uses 0.8% NAV; if negative/credit, use small positive proxy.
    width=max(Kf-Kn,1.0)
    risk=max((width*Ns-max(0.,-debit/100))*100,1.0)
    n=math.floor(nav*RISK_BUDGET/risk)
    return {'Kf':Kf,'Kn':Kn,'target':target,'n':n,'far_bid':fbid,'near_ask':nask,'debit':debit,'risk':risk}

def target_from_state(far_delta_abs, distance_pct, gamma_rel, delta_jump, Ns):
    dscore=1 if far_delta_abs<.04 else 2 if far_delta_abs<.06 else 3 if far_delta_abs<.08 else 4 if far_delta_abs<.10 else 5
    xscore=1 if distance_pct>.10 else 2 if distance_pct>.07 else 3 if distance_pct>.04 else 4 if distance_pct>.02 else 5
    gscore=1 if gamma_rel<1.20 and delta_jump<.01 else 2 if gamma_rel<1.50 and delta_jump<.02 else 3
    base=int(math.ceil(COVERAGE_MULT*Ns*far_delta_abs/LONG_DELTA))
    comp=.5*dscore+.3*xscore+.2*gscore
    boost=2 if comp>=4.2 else 1 if comp>=3.2 else 0
    return max(1,min(MAX_STACK,base+boost)),{'dscore':dscore,'xscore':xscore,'gscore':gscore,'risk_score':comp}

def simulate(path,Ns):
    d=json.load(open(path,encoding='utf-8'))
    df=pd.DataFrame({'date':pd.to_datetime(d['dates']),'qqq':d['c']['QQQ'],'vxx':d['c']['VXX'],'vix':d['c']['VIX']})
    df=df[(df.date>=pd.Timestamp('2018-03-01'))&(df.date<=pd.Timestamp('2026-09-04'))].dropna().reset_index(drop=True)
    df['rQ']=df.qqq.pct_change().fillna(0); df['rV']=df.vxx.pct_change().fillna(0)
    df['vixma']=df.vix.rolling(20).mean(); df['ts']=np.tanh((df.vixma-df.vix)/6)*.1
    cash=CAPITAL; core_n=0; far=None; near=[]; vshort=None; vcc=None; eq=[]; events=[]; peak=CAPITAL
    for i,row in df.iterrows():
        nav=cash + row.qqq*core_n
        # Close far/near package at 21-session life or adverse state.
        if far is not None:
            dte=max(far['expiry']-i,0); Kf=far['Kf']; Kn=far['Kn']; nfar=far['nfar']; nn=far['nnear']
            sigf=far['sigf']; sign=far['sign']
            Tfar=max(dte/365,1/365); Tnear=max((far['expiry_near']-i)/365,1/365)
            fask=call(row.qqq,Kf,Tfar,.03,sigf,.004)*(1+sprq(row.vix))
            nbid=call(row.qqq,Kn,Tnear,.03,sign,.004)*(1-sprq(row.vix))
            pnl=(far['nnear']*(nbid-far['entry_near'])-nfar*(fask-far['entry_far']))*100
            risk=far['risk']
            fire=dte<=7 or (pnl/risk>=.5) or (pnl/risk<=-.55)
            if fire:
                cash += nn*nbid*100 - nfar*fask*100
                events.append({'date':str(row.date.date()),'event':'CLOSE_FAR_NEAR','Ns':Ns,'pnl':float(pnl),'reason':'RISK_OR_DTE'})
                far=None; near=[]
        # vxx layers follow source-aligned shock policy.
        shock=(row.rV>.06 or row.vix>35 or row.ts<0 or row.rQ<-.03)
        if vshort is not None:
            dte=max(vshort['expiry']-i,0)
            pnl=(vshort['S0']-row.vxx)*vshort['n']; fire=shock or dte<=7 or pnl/(vshort['S0']*vshort['n'])<=-.5
            if fire:
                cash += -row.vxx*vshort['n']; vshort=None
        if vcc is not None:
            dte=max(vcc['expiry']-i,0); S=row.vxx; T=max(dte/365,1/365)
            Ks,Kw,credit=vcc['Ks'],vcc['Kl'],vcc['credit']; h=sprv(row.vix)
            px=call(S,Ks,T,.03,ivvc(row.vix),0)*(1+h)-call(S,Kw,T,.03,ivvc(row.vix)*.96,0)*(1-h)
            pnl=(credit-px)*100*vcc['n']; risk=vcc['risk']
            if shock or dte<=7 or pnl/risk>=.5 or pnl/risk<=-.55:
                cash += -px*100*vcc['n']; vcc=None
        nav=cash+row.qqq*core_n
        # Core 42%
        if core_n==0:
            core_n=math.floor(nav*CORE_FRAC/row.qqq); cash-=core_n*row.qqq
        # Open/reload QQQ FAR+near package.
        if far is None:
            sigf=ivq(row.vix)*.95
            Kf,fbid,fask,sigf=qqq_far(row.qqq,row.vix,FAR_DTE/365)
            Kn,nbid,nask,sign=qqq_near(row.qqq,row.vix,NEAR_DTE/365)
            # state at entry, using exact causal values available on the day.
            dist=(Kf-row.qqq)/row.qqq
            desired,state=target_from_state(FAR_DELTA,dist,1.0,0.0,Ns)
            risk=max((Kf-Kn)*Ns*100,100.0)
            n_struct=max(1,math.floor(nav*RISK_BUDGET/risk))
            nfar=Ns*n_struct; nnear=desired*n_struct
            cash += nfar*fbid*100 - nnear*nask*100
            far={'Kf':Kf,'Kn':Kn,'nfar':nfar,'nnear':nnear,'entry_far':fbid,'entry_near':nask,'sigf':sigf,'sign':sign,'risk':risk*n_struct,'expiry':i+21,'expiry_near':i+21}
            events.append({'date':str(row.date.date()),'event':'OPEN_FAR_NEAR','Ns':Ns,'nfar':nfar,'nnear':nnear})
        if vshort is None and not shock and row.ts>=0:
            n=max(1,math.floor(nav*VXX_SHORT_FRAC/row.vxx)); cash+=row.vxx*n; vshort={'S0':row.vxx,'n':n,'expiry':i+21}
        if vcc is None and not shock and row.ts>=0:
            Ks,Kw,credit=vxx_cc(row.vxx,row.vix,30/365); risk=max((Kw-Ks-credit)*100,100); n=max(1,math.floor(nav*VXX_CC_RISK/risk)); cash+=credit*100*n; vcc={'Ks':Ks,'Kl':Kw,'credit':credit,'risk':risk*n,'n':n,'expiry':i+21}
        nav=cash+row.qqq*core_n
        eq.append((row.date,nav))
        peak=max(peak,nav)
    e=pd.DataFrame(eq,columns=['date','nav']); e['peak']=e.nav.cummax(); e['dd']=e.nav/e.peak-1
    years=(e.date.iloc[-1]-e.date.iloc[0]).days/365.25
    cagr=(e.nav.iloc[-1]/CAPITAL)**(1/years)-1
    return {'Ns':Ns,'cagr':float(cagr),'maxdd':float(e.dd.min()),'final_nav':float(e.nav.iloc[-1]),'years':float(years),'events':len(events)},e

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--spots-path',required=True); ap.add_argument('--out',default='artifacts'); a=ap.parse_args()
    out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    rows=[]; curves={}
    for Ns in (10,5):
        s,e=simulate(a.spots_path,Ns); rows.append(s); curves[Ns]=e; e.to_csv(out/f'hybrid_far{Ns}_equity.csv',index=False)
    df=pd.DataFrame(rows); df.to_csv(out/'hybrid_far5_vs_far10_summary.csv',index=False)
    base=df[df.Ns==10].iloc[0]; red=df[df.Ns==5].iloc[0]
    report={'research_id':'QQQ_HYBRID_FAR5_COMPARISON_V1','status':'DERIVED_REPLAY','pricing_model':'DERIVED_BS_VIX','not_opra':True,'data_sha256':hashlib.sha256(open(a.spots_path,'rb').read()).hexdigest(),'window':['2018-03-01','2026-09-04'],'contract_definition':{'far_short_delta':FAR_DELTA,'far_dte_days':FAR_DTE,'near_long_delta':LONG_DELTA,'near_dte_days':NEAR_DTE,'coverage_mult':COVERAGE_MULT,'risk_budget':RISK_BUDGET,'far_counts_compared':[10,5]},'results':rows,'delta_5_minus_10':{'cagr':float(red.cagr-base.cagr),'maxdd':float(red.maxdd-base.maxdd),'final_nav':float(red.final_nav-base.final_nav)},'note':'N=5 is defined strictly as five FAR short calls per structural unit versus N=10; all other stated parameters/path are frozen. Derived BS/VIX, not OPRA.'}
    (out/'qqq_hybrid_far5_comparison_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
