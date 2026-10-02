import argparse, hashlib, json, math, numpy as np, pandas as pd
from math import erf,sqrt,exp,log
from scipy.stats import norm

CAPITAL=100000.0
BASE_QCC_RISK=0.008
BASE_RV=0.02
DD_HALF=-0.10
PROFIT_HALF=0.30
DELTA_HALF=0.30
DELTA_ZERO=0.40
R5_HALF=0.06
R10_ZERO=0.10
HIGH52_HALF=0.99
HIGH52_ZERO=0.995
APPROACH=.98


def N(x): return 0.5*(1+erf(x/sqrt(2)))
def d1d2(S,K,T,r,sig,q=0):
    vs=sig*sqrt(max(T,1e-8)); d1=(log(S/K)+(r-q+0.5*sig*sig)*T)/vs; return d1,d1-vs
def bsCall(S,K,T,r,sig,q=0):
    if T<=1/365 or sig<1e-8:return max(S-K,0)
    d1,d2=d1d2(S,K,T,r,sig,q);return S*exp(-q*T)*N(d1)-K*exp(-r*T)*N(d2)
def bsDelta(S,K,T,r,sig,q=0):
    if T<=1/365 or sig<1e-8:return 1.0 if S>K else 0.0
    d1,_=d1d2(S,K,T,r,sig,q);return exp(-q*T)*N(d1)
def strikeFromCallDelta(S,T,r,q,sig,target):
    p=min(max(target*exp(q*T),1e-6),1-1e-6); d1=norm.ppf(p);vs=sig*sqrt(T)
    return max(S*exp(-(d1*vs-(r-q+0.5*sig*sig)*T)),1e-6)
def ivVxx(vix): return min(max(.48+1.35*(vix/100),.42),1.8)
def ivQqq(vix): return min(max(1.08*(vix/100),.1),.9)
def halfSpreadV(vix): return min(max(.035+.14*max(vix/100-.16,0),.03),.16)
def halfSpreadQ(vix): return min(max(.025+.08*max(vix/100-.16,0),.02),.1)
def ivVxxCall(vix): return min(ivVxx(vix)*1.12,2.2)
def quoteCC(S,vix,T,kind,half):
    if kind=='vxx': sigS=ivVxxCall(vix);sigL=sigS*.96;q=0
    else: sigS=ivQqq(vix)*.95;sigL=ivQqq(vix)*.9;q=.004
    Ks=strikeFromCallDelta(S,T,.03,q,sigS,.35 if kind=='vxx' else .16)
    Kl=strikeFromCallDelta(S,T,.03,q,sigL,.16 if kind=='vxx' else .08)
    if Kl<=Ks:Kl=Ks*(1.14 if kind=='vxx' else 1.06)
    midS=bsCall(S,Ks,T,.03,sigS,q);midL=bsCall(S,Kl,T,.03,sigL,q)
    credit=max(midS*(1-half)-midL*(1+half),1e-4)
    return {'Ks':Ks,'Kl':Kl,'premium':credit,'width':Kl-Ks}

def qcc_mark(row,p,i):
    S=row.qqq;half=halfSpreadQ(row.vix);sigS=ivQqq(row.vix)*.95;sigL=ivQqq(row.vix)*.9;T=max((p['expiry_i']-i)/365,1/365)
    exitp=bsCall(S,p['Ks'],T,.03,sigS,.004)*(1+half)-bsCall(S,p['Kl'],T,.03,sigL,.004)*(1-half)
    pnl_per=(p['premium']-exitp)*100; risk_per=(p['width']-p['premium'])*100
    delta=bsDelta(S,p['Ks'],T,.03,sigS,.004)
    return exitp,pnl_per,risk_per,delta

def qcc_close_prices(row,p,i):
    half=halfSpreadQ(row.vix);sigS=ivQqq(row.vix)*.95;sigL=ivQqq(row.vix)*.9;T=max((p['expiry_i']-i)/365,1/365)
    askS=bsCall(row.qqq,p['Ks'],T,.03,sigS,.004)*(1+half)
    bidW=bsCall(row.qqq,p['Kl'],T,.03,sigL,.004)*(1-half)
    return askS,bidW

def portfolio_liq(df,i,legs):
    row=df.iloc[i];liq=0
    for p in legs:
        dte=max(p['expiry_i']-i,0)
        if p['structure']=='qqq-long':liq+=row.qqq*p['n']
        elif p['structure']=='vxx-short':liq+=-row.vxx*p['n']
        else:
            kind=p['kind'];S=row.vxx if kind=='vxx' else row.qqq;half=halfSpreadV(row.vix) if kind=='vxx' else halfSpreadQ(row.vix);qvol=0 if kind=='vxx' else .004;sigS=ivVxxCall(row.vix) if kind=='vxx' else ivQqq(row.vix)*.95;sigL=sigS*.96 if kind=='vxx' else ivQqq(row.vix)*.9;T=max(dte/365,1/365);exitp=bsCall(S,p['Ks'],T,.03,sigS,qvol)*(1+half)-bsCall(S,p['Kl'],T,.03,sigL,qvol)*(1-half);liq+=-exitp*100*p['n']
    return liq

def target_fraction(row, dd, qcc_info=None, breakout_zero=False):
    target=BASE_QCC_RISK; reasons=[]
    if dd<=DD_HALF: target=min(target,BASE_QCC_RISK/2); reasons.append('PORTFOLIO_DD')
    high52=float(row.high52) if pd.notna(row.high52) else 0.0
    if high52>0 and row.qqq>=HIGH52_HALF*high52: target=min(target,BASE_QCC_RISK/2); reasons.append('HEAT_52W')
    if row.r5>=R5_HALF: target=min(target,BASE_QCC_RISK/2); reasons.append('ACCELERATION_5D')
    if qcc_info is not None:
        _,pnl,risk,delta=qcc_info
        pnl_pct=pnl/risk if risk>0 else 0.0
        if pnl_pct>=PROFIT_HALF: target=min(target,BASE_QCC_RISK/2); reasons.append('PROFIT_RECOVERY')
        if delta>=DELTA_HALF: target=min(target,BASE_QCC_RISK/2); reasons.append('SHORT_DELTA')
        if delta>=DELTA_ZERO: target=0.0; reasons.append('DELTA_ZERO')
    if row.r10>=R10_ZERO and high52>0 and row.qqq>=HIGH52_ZERO*high52:
        target=0.0; reasons.append('STRONG_BREAKOUT_ZERO')
    if breakout_zero:
        target=0.0; reasons.append('BREAKOUT_CONTINUATION')
    return target,reasons

def sha256_file(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def simulate(spots_path, dynamic=False, include=None):
    data=json.load(open(spots_path, encoding='utf-8'))
    if not {'dates','c'}.issubset(data):
        raise ValueError('Input JSON must contain dates and c series map')
    include = include or {'core': True, 'qcc': True, 'vxx_short': True, 'vxx_cc': True}
    df=pd.DataFrame({'date':pd.to_datetime(data['dates']),'qqq':data['c']['QQQ'],'vxx':data['c']['VXX'],'vix':data['c']['VIX']})
    df=df[(df['date']>=pd.Timestamp('2018-03-01')) & (df['date']<=pd.Timestamp('2026-09-04'))].copy()
    missing=df.loc[df[['qqq','vxx','vix']].isna().any(axis=1),'date'].dt.strftime('%Y-%m-%d').tolist()
    df=df.dropna(subset=['qqq','vxx','vix']).reset_index(drop=True)
    df['rQ']=df.qqq.pct_change().fillna(0);df['rV']=df.vxx.pct_change().fillna(0)
    df['hv20q']=df.rQ.rolling(20,min_periods=1).std().fillna(.2)*math.sqrt(252)
    df['vixma']=df.vix.rolling(20,min_periods=1).mean();df['ts']=np.tanh((df.vixma-df.vix)/6)*.1
    df['r5']=df.qqq.pct_change(5).fillna(0);df['r10']=df.qqq.pct_change(10).fillna(0);df['high52']=df.qqq.rolling(252,min_periods=1).max()
    cash_box=[CAPITAL];legs=[];eq=[];opens=[];closes=[];events=[];peak=CAPITAL;approach=None;qcc_block_until=-1; deploy_state=BASE_QCC_RISK; deploy_up_streak=0
    for i,row in df.iterrows():
        keep=[]
        for p in legs:
            dte=max(p['expiry_i']-i,0)
            if p['structure']=='qqq-long':
                keep.append(p)
            elif p['structure']=='vxx-short':
                pnl=(p['S0']-row.vxx)*p['n'];liq=-row.vxx*p['n'];fire=(row.rV>.06 or row.vix>35 or row.ts<0 or dte<=7 or (pnl/(p['S0']*p['n'])<=-0.5))
                if fire: cash_box[0]+=liq;closes.append((row.date,p['structure'],p['n'],pnl))
                else:keep.append(p)
            else:
                kind=p['kind'];S=row.vxx if kind=='vxx' else row.qqq;half=halfSpreadV(row.vix) if kind=='vxx' else halfSpreadQ(row.vix);qvol=0 if kind=='vxx' else .004;sigS=ivVxxCall(row.vix) if kind=='vxx' else ivQqq(row.vix)*.95;sigL=sigS*.96 if kind=='vxx' else ivQqq(row.vix)*.9;T=max(dte/365,1/365);exitp=bsCall(S,p['Ks'],T,.03,sigS,qvol)*(1+half)-bsCall(S,p['Kl'],T,.03,sigL,qvol)*(1-half);pnl=(p['premium']-exitp)*100*p['n'];liq=-exitp*100*p['n'];risk=(p['width']-p['premium'])*100*p['n'];fire=(dte<=7 or (pnl/risk<=-0.55) or (pnl/risk>=.5))
                if fire: cash_box[0]+=liq;closes.append((row.date,p['structure'],p['n'],pnl));events.append({'date':str(row.date.date()),'event':'CLOSE_QCC_ROLL','n':int(p['n']),'pnl':float(pnl)})
                else:keep.append(p)
        legs=keep
        nav=cash_box[0]+portfolio_liq(df,i,legs);peak=max(peak,nav);dd=nav/peak-1
        breakout_zero=False
        skip_qcc_open_today=False
        qcc=next((p for p in legs if p['structure']=='qqq-cc'),None)
        if dynamic and qcc is not None:
            approach_now=row.qqq>=APPROACH*qcc['Ks']
            if approach_now and approach is None:
                approach={'i':i,'close':float(row.qqq),'Ks':float(qcc['Ks'])}
            elif approach is not None and i==approach['i']+1:
                if row.qqq>=approach['close']:
                    breakout_zero=True
                else:
                    approach=None
            elif not approach_now:
                approach=None
            raw_target,reasons=target_fraction(row,dd,qcc_mark(row,qcc,i),breakout_zero)
            if raw_target < deploy_state:
                deploy_state=raw_target; deploy_up_streak=0
            elif raw_target > deploy_state:
                deploy_up_streak += 1
                if deploy_up_streak >= 2:
                    deploy_state=min(raw_target, deploy_state + BASE_QCC_RISK/2); deploy_up_streak=0
            else:
                deploy_up_streak=0
            target=deploy_state
            desired=math.floor(nav*target/(qcc['width']-qcc['premium'])/100)
            cur=qcc['n']
            if desired<cur:
                askS,bidW=qcc_close_prices(row,qcc,i);nclose=cur-desired;cash_box[0]+=(-askS+bidW)*100*nclose;qcc['n']=desired;events.append({'date':str(row.date.date()),'event':'DYNAMIC_DELEVERAGE','n':nclose,'to_n':desired,'target_frac':target,'reasons':reasons})
                if qcc['n']==0:
                    legs=[x for x in legs if x is not qcc]; qcc_block_until=i+1; skip_qcc_open_today=True
            elif desired>cur:
                half=halfSpreadQ(row.vix);sigS=ivQqq(row.vix)*.95;sigL=ivQqq(row.vix)*.9;T=max((qcc['expiry_i']-i)/365,1/365);short_bid=bsCall(row.qqq,qcc['Ks'],T,.03,sigS,.004)*(1-half);wing_ask=bsCall(row.qqq,qcc['Kl'],T,.03,sigL,.004)*(1+half);credit=max(short_bid-wing_ask,1e-4);nadd=desired-cur;oldn=cur;qcc['premium']=(qcc['premium']*oldn+credit*nadd)/desired;qcc['n']=desired;cash_box[0]+=credit*100*nadd;events.append({'date':str(row.date.date()),'event':'DYNAMIC_REDEPLOY','n':nadd,'to_n':desired,'target_frac':target,'reasons':reasons})
            if breakout_zero and qcc['n']==0:
                approach=None
        state='Shock' if (row.rV>.06 or row.vix>35 or row.rQ<-.03) else ('High-Spread' if halfSpreadV(row.vix)>.14 else ('Decay-Optimal' if row.ts>=0 and row.vix<28 else 'Normal'))
        wantV=state!='Shock' and row.ts>=0
        nav=cash_box[0]+portfolio_liq(df,i,legs)
        structs={p['structure'] for p in legs}
        def open_leg(st,frac):
            if st in structs or frac<=0:return
            if st=='qqq-long':
                n=math.floor(nav*frac/row.qqq)
                if n: cash_box[0]-=row.qqq*n;legs.append({'structure':st,'n':n,'S0':row.qqq,'expiry_i':i+100000});opens.append((row.date,st,n))
            elif st=='vxx-short':
                n=math.floor(nav*frac/row.vxx)
                if n: cash_box[0]+=row.vxx*n;legs.append({'structure':st,'n':n,'S0':row.vxx,'expiry_i':i+21});opens.append((row.date,st,n))
            else:
                kind='vxx' if st=='vxx-cc' else 'qqq';half=halfSpreadV(row.vix) if kind=='vxx' else halfSpreadQ(row.vix);q=quoteCC(row.vxx if kind=='vxx' else row.qqq,row.vix,30/365,kind,half);frac_use=BASE_QCC_RISK if kind=='qqq' else BASE_RV;n=math.floor(nav*frac_use/((q['width']-q['premium'])*100))
                if n: cash_box[0]+=q['premium']*100*n;legs.append({'structure':st,'kind':kind,'n':n,'S0':row.vxx if kind=='vxx' else row.qqq,'Ks':q['Ks'],'Kl':q['Kl'],'premium':q['premium'],'width':q['width'],'expiry_i':i+21});opens.append((row.date,st,n));events.append({'date':str(row.date.date()),'event':'OPEN_'+st.replace('-','_'),'n':int(n),'target_frac':float(frac_use)})
        if include.get('core', True):
            open_leg('qqq-long',.42)
        if dynamic:
            if i>=qcc_block_until and not skip_qcc_open_today:
                raw_target,_=target_fraction(row,dd,None,False)
                if raw_target < deploy_state:
                    deploy_state=raw_target; deploy_up_streak=0
                elif raw_target > deploy_state:
                    deploy_up_streak += 1
                    if deploy_up_streak >= 2:
                        deploy_state=min(raw_target, deploy_state + BASE_QCC_RISK/2); deploy_up_streak=0
                else:
                    deploy_up_streak=0
                open_leg('qqq-cc',deploy_state)
        else:
            if include.get('qcc', True):
                open_leg('qqq-cc',.008)
        if wantV:
            if include.get('vxx_short', True):
                open_leg('vxx-short',.18)
            if include.get('vxx_cc', True):
                open_leg('vxx-cc',.02)
        nav=cash_box[0]+portfolio_liq(df,i,legs)
        eq.append((row.date,nav))
    e=pd.DataFrame(eq,columns=['date','nav']);e['peak']=e.nav.cummax();e['dd']=e.nav/e.peak-1
    years=(e.date.iloc[-1]-e.date.iloc[0]).days/365.25;cagr=(e.nav.iloc[-1]/CAPITAL)**(1/years)-1
    return cagr,e.dd.min(),e.nav.iloc[-1],opens,closes,events,e


def split_stats(eqdf, start, end):
    x=eqdf[(eqdf["date"]>=pd.Timestamp(start)) & (eqdf["date"]<=pd.Timestamp(end))].copy().sort_values("date")
    if x.empty: return {"start":start,"end":end,"status":"NO_DATA"}
    x["peak"]=x["nav"].cummax(); x["dd"]=x["nav"]/x["peak"]-1
    start_nav=float(x["nav"].iloc[0]); end_nav=float(x["nav"].iloc[-1])
    total=end_nav/start_nav-1
    years=max((x["date"].iloc[-1]-x["date"].iloc[0]).days/365.25,1/365.25)
    cagr=(end_nav/start_nav)**(1/years)-1 if end_nav>0 else -1
    return {"start":start,"end":end,"start_nav":start_nav,"end_nav":end_nav,"return":total,"cagr":cagr,"maxdd_daily_mtm":float(x["dd"].min()),"days":int((x["date"].iloc[-1]-x["date"].iloc[0]).days)}


def shapley(values):
    layers = ['core','qcc','vxx_short','vxx_cc']
    full = values[(1,1,1,1)]['final_nav']
    out = {}
    import itertools, math
    for i, layer in enumerate(layers):
        others=[j for j in range(4) if j!=i]
        total=0.0
        for r in range(4):
            for comb in itertools.combinations(others,r):
                m0=[0]*4
                for j in comb: m0[j]=1
                m1=m0.copy(); m1[i]=1
                v0=values[tuple(m0)]['final_nav']; v1=values[tuple(m1)]['final_nav']
                w=math.factorial(r)*math.factorial(3-r)/math.factorial(4)
                total += w*(v1-v0)
        out[layer]=total
    return out

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--spots-path', required=True)
    ap.add_argument('--out', default='artifacts')
    args=ap.parse_args()
    out=__import__('pathlib').Path(args.out); out.mkdir(parents=True,exist_ok=True)
    layers=['core','qcc','vxx_short','vxx_cc']
    values={}; rows=[]
    for mask in __import__('itertools').product([0,1], repeat=4):
        inc=dict(zip(layers,[bool(x) for x in mask]))
        cagr,maxdd,final_nav,opens,closes,events,e=simulate(args.spots_path,False,inc)
        s={'cagr':cagr,'maxdd_daily_mtm':maxdd,'final_nav':final_nav,'opens':len(opens),'closes':len(closes),'events':len(events)}
        values[mask]=s
        rows.append({'mask':''.join(map(str,mask)),**s,**inc})
        e.to_csv(out/f"equity_mask_{''.join(map(str,mask))}.csv",index=False)
    pd.DataFrame(rows).sort_values('mask').to_csv(out/'component_ablation.csv',index=False)
    full=values[(1,1,1,1)]
    loo=[]
    for i,layer in enumerate(layers):
        mask=[1]*4; mask[i]=0; mask=tuple(mask)
        s=values[mask]
        loo.append({'layer':layer,'full_final_nav':full['final_nav'],'without_final_nav':s['final_nav'],'delta_final_nav':full['final_nav']-s['final_nav'],'full_cagr':full['cagr'],'without_cagr':s['cagr'],'delta_cagr':full['cagr']-s['cagr'],'full_maxdd':full['maxdd_daily_mtm'],'without_maxdd':s['maxdd_daily_mtm']})
    pd.DataFrame(loo).to_csv(out/'component_leave_one_out.csv',index=False)
    sh=shapley(values)
    pd.DataFrame([{'layer':k,'shapley_delta_final_nav':v} for k,v in sh.items()]).to_csv(out/'component_shapley_final_nav.csv',index=False)
    report={'research_id':'QQQ_HYBRID_COMPONENT_DECOMPOSITION_V1','status':'DERIVED_REPLAY','pricing_model':'DERIVED_BS_VIX','not_opra':True,'data_sha256':sha256_file(args.spots_path),'rules':{'source_logic_control':'exact repo-fixture adaptation of QQQ_HYBRID_DYNAMIC_DEPLOYMENT_V1_1','no_parameter_search':True,'window':'2018-03-01 to 2026-09-04','missing_rows':'drop synchronized market holiday rows only; no fill'},'full':full,'leave_one_out':loo,'shapley_final_nav':sh,'fixture_note':'Canonical universe fixture has QQQ/VXX null on 2026-05-25; that calendar row is excluded consistently from every mask.'}
    (out/'qqq_hybrid_component_decomposition_v1_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
