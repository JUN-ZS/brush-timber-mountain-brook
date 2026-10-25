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

def tail_trigger(row):
    """Frozen end-of-day trigger inherited from Original Hybrid's VXX shock exits."""
    return bool(float(row.rV) > 0.06 or float(row.vix) > 35.0 or float(row.ts) < 0.0 or float(row.rQ) < -0.03)


def tail_mark_value(position, adjusted_close):
    if position is None:
        return 0.0
    return float(position["entry_notional"]) * float(adjusted_close) / float(position["entry_adj_close"])


def simulate(spots_path, dynamic=False, tail_prices_path=None, tail_mode="NONE",
             tail_budget_pct=0.0, tail_friction_bps=10.0, legacy_qqq_cash_bug=False):
    data=json.load(open(spots_path, encoding='utf-8'))
    if not {'dates','qqq','vxx','vix'}.issubset(data):
        raise ValueError('Input JSON must contain dates, qqq, vxx, vix arrays')
    df=pd.DataFrame({'date':pd.to_datetime(data['dates']),'qqq':data['qqq'],'vxx':data['vxx'],'vix':data['vix']})
    if tail_prices_path is not None:
        tp=pd.read_csv(tail_prices_path,parse_dates=['date'])
        if not {'date','adj_close'}.issubset(tp.columns):
            raise ValueError('TAIL CSV must contain date,adj_close')
        tp=tp[['date','adj_close']].rename(columns={'adj_close':'tail_adj_close'})
        tp=tp.dropna().drop_duplicates('date').sort_values('date')
        df=df.merge(tp,on='date',how='inner',validate='one_to_one')
    else:
        df['tail_adj_close']=np.nan
    df=df.sort_values('date').drop_duplicates('date').reset_index(drop=True)
    if df.empty:
        raise ValueError('No common QQQ/VXX/VIX and TAIL dates')
    if tail_mode not in {'NONE','TRIGGERED','ALWAYS_ON'}:
        raise ValueError('tail_mode must be NONE, TRIGGERED or ALWAYS_ON')
    if not 0 <= float(tail_budget_pct) <= 0.20:
        raise ValueError('TAIL initial allocation must be between 0% and 20% of NAV')
    if not 0 <= float(tail_friction_bps) <= 100:
        raise ValueError('TAIL round-trip friction must be between 0 and 100 bps')

    df['rQ']=df.qqq.pct_change().fillna(0);df['rV']=df.vxx.pct_change().fillna(0)
    df['hv20q']=df.rQ.rolling(20,min_periods=1).std().fillna(.2)*math.sqrt(252)
    df['vixma']=df.vix.rolling(20,min_periods=1).mean();df['ts']=np.tanh((df.vixma-df.vix)/6)*.1
    df['r5']=df.qqq.pct_change(5).fillna(0);df['r10']=df.qqq.pct_change(10).fillna(0);df['high52']=df.qqq.rolling(252,min_periods=1).max()

    cash_box=[CAPITAL];legs=[];eq=[];opens=[];closes=[];events=[];peak=CAPITAL;approach=None;qcc_block_until=-1; deploy_state=BASE_QCC_RISK; deploy_up_streak=0
    tail_pos=None;tail_trades=[];tail_events=[];tail_calm_streak=0
    tail_entry_scheduled=(tail_mode=='ALWAYS_ON')
    tail_exit_scheduled=False
    friction_rate=float(tail_friction_bps)/10000.0
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

        # Signals are formed at a close and executed at the next common session close.
        tail_px=float(row.tail_adj_close)
        if tail_exit_scheduled and tail_pos is not None:
            exit_value=tail_mark_value(tail_pos,tail_px)
            exit_fee=exit_value*friction_rate/2
            cash_box[0]+=exit_value-exit_fee
            trade=tail_trades[tail_pos['trade_index']]
            trade.update({'exit_date':str(row.date.date()),'exit_adj_close':tail_px,
                'exit_value_usd':float(exit_value),'exit_fee_usd':float(exit_fee),
                'net_pnl_usd':float(exit_value-tail_pos['entry_notional']-tail_pos['entry_fee_usd']-exit_fee),
                'status':'CLOSED'})
            tail_events.append({'date':str(row.date.date()),'event':'TAIL_EXIT',
                'reason':'TWO_CONSECUTIVE_CALM_CLOSES_CONFIRMED_PREVIOUS_SESSION',
                'value_usd':float(exit_value),'fee_usd':float(exit_fee)})
            tail_pos=None;tail_exit_scheduled=False;tail_calm_streak=0

        if tail_entry_scheduled and tail_pos is None and tail_mode!='NONE':
            nav_pre_entry=cash_box[0]+portfolio_liq(df,i,legs)
            entry_notional=max(0.0,float(nav_pre_entry)*float(tail_budget_pct))
            if entry_notional>0 and tail_px>0:
                entry_fee=entry_notional*friction_rate/2
                cash_box[0]-=(entry_notional+entry_fee)
                trade_index=len(tail_trades)
                tail_pos={'entry_notional':float(entry_notional),'entry_adj_close':float(tail_px),
                    'entry_fee_usd':float(entry_fee),'entry_date':str(row.date.date()),'trade_index':trade_index}
                tail_trades.append({'entry_date':str(row.date.date()),'entry_adj_close':float(tail_px),
                    'entry_notional_usd':float(entry_notional),'entry_fee_usd':float(entry_fee),
                    'exit_date':'','exit_adj_close':None,'exit_value_usd':None,'exit_fee_usd':None,
                    'net_pnl_usd':None,'status':'OPEN_AT_END'})
                tail_events.append({'date':str(row.date.date()),'event':'TAIL_ENTRY',
                    'reason':'ALWAYS_ON' if tail_mode=='ALWAYS_ON' else 'PREVIOUS_CLOSE_TRIGGER',
                    'notional_usd':float(entry_notional),'fee_usd':float(entry_fee)})
            tail_entry_scheduled=False
        tail_mv_current=tail_mark_value(tail_pos,tail_px)

        nav=cash_box[0]+portfolio_liq(df,i,legs)+tail_mv_current;peak=max(peak,nav);dd=nav/peak-1
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
        nav=cash_box[0]+portfolio_liq(df,i,legs)+tail_mv_current
        structs={p['structure'] for p in legs}
        def open_leg(st,frac):
            if st in structs or frac<=0:return
            if st=='qqq-long':
                n=math.floor(nav*frac/row.qqq)
                if n:
                    if legacy_qqq_cash_bug:
                        # Forensic control only: reproduce the inherited missing cash debit.
                        cash_box[0]-row.qqq*n
                    else:
                        cash_box[0]-=row.qqq*n
                    legs.append({'structure':st,'n':n,'S0':row.qqq,'expiry_i':i+100000})
                    opens.append((row.date,st,n))
            elif st=='vxx-short':
                n=math.floor(nav*frac/row.vxx)
                if n: cash_box[0]+=row.vxx*n;legs.append({'structure':st,'n':n,'S0':row.vxx,'expiry_i':i+21});opens.append((row.date,st,n))
            else:
                kind='vxx' if st=='vxx-cc' else 'qqq';half=halfSpreadV(row.vix) if kind=='vxx' else halfSpreadQ(row.vix);q=quoteCC(row.vxx if kind=='vxx' else row.qqq,row.vix,30/365,kind,half);frac_use=BASE_QCC_RISK if kind=='qqq' else BASE_RV;n=math.floor(nav*frac_use/((q['width']-q['premium'])*100))
                if n: cash_box[0]+=q['premium']*100*n;legs.append({'structure':st,'kind':kind,'n':n,'S0':row.vxx if kind=='vxx' else row.qqq,'Ks':q['Ks'],'Kl':q['Kl'],'premium':q['premium'],'width':q['width'],'expiry_i':i+21});opens.append((row.date,st,n));events.append({'date':str(row.date.date()),'event':'OPEN_'+st.replace('-','_'),'n':int(n),'target_frac':float(frac_use)})
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
            open_leg('qqq-cc',.008)
        if wantV:open_leg('vxx-short',.18);open_leg('vxx-cc',.02)
        nav=cash_box[0]+portfolio_liq(df,i,legs)+tail_mv_current

        trigger=tail_trigger(row)
        if tail_mode=='TRIGGERED':
            if trigger:
                tail_calm_streak=0
                if tail_pos is None and not tail_entry_scheduled:
                    tail_entry_scheduled=True
            else:
                tail_calm_streak+=1
                if tail_pos is not None and tail_calm_streak>=2:
                    tail_exit_scheduled=True

        eq.append((row.date,nav,tail_mv_current,float(cash_box[0]),bool(trigger),bool(tail_pos is not None)))
    e=pd.DataFrame(eq,columns=['date','nav','tail_market_value','cash','tail_trigger','tail_open'])
    e['peak']=e.nav.cummax();e['dd']=e.nav/e.peak-1
    years=(e.date.iloc[-1]-e.date.iloc[0]).days/365.25;cagr=(e.nav.iloc[-1]/CAPITAL)**(1/years)-1
    if tail_pos is not None:
        last_px=float(df.iloc[-1].tail_adj_close)
        last_mv=tail_mark_value(tail_pos,last_px)
        trade=tail_trades[tail_pos['trade_index']]
        trade.update({'exit_date':'','exit_adj_close':float(last_px),'exit_value_usd':float(last_mv),
            'exit_fee_usd':0.0,'net_pnl_usd':float(last_mv-tail_pos['entry_notional']-tail_pos['entry_fee_usd']),
            'status':'MARKED_OPEN_AT_END'})
    return cagr,float(e.dd.min()),float(e.nav.iloc[-1]),opens,closes,events,e,tail_trades

def split_stats(eqdf, start, end):
    x=eqdf[(eqdf["date"]>=pd.Timestamp(start)) & (eqdf["date"]<=pd.Timestamp(end))].copy().sort_values("date")
    if x.empty: return {"start":start,"end":end,"status":"NO_DATA"}
    x["peak"]=x["nav"].cummax(); x["dd"]=x["nav"]/x["peak"]-1
    start_nav=float(x["nav"].iloc[0]); end_nav=float(x["nav"].iloc[-1])
    total=end_nav/start_nav-1
    years=max((x["date"].iloc[-1]-x["date"].iloc[0]).days/365.25,1/365.25)
    cagr=(end_nav/start_nav)**(1/years)-1 if end_nav>0 else -1
    return {"start":start,"end":end,"start_nav":start_nav,"end_nav":end_nav,"return":total,"cagr":cagr,"maxdd_daily_mtm":float(x["dd"].min()),"days":int((x["date"].iloc[-1]-x["date"].iloc[0]).days)}

if __name__=='__main__':
    ap=argparse.ArgumentParser(description='Frozen Original Hybrid + TAIL account-NAV overlay replay')
    ap.add_argument('--spots-path',required=True)
    ap.add_argument('--tail-prices-path',required=True)
    ap.add_argument('--out',default='research/qqq_hybrid_tail_triggered_nav_v1/results/latest')
    ap.add_argument('--friction-bps',type=float,default=10.0)
    args=ap.parse_args()
    from pathlib import Path
    inherited_path=Path(__file__).with_name('qqq_hybrid_dynamic_deployment_v1_1_replay.py')
    inherited_bytes=inherited_path.read_bytes()
    inherited_blob_sha1=hashlib.sha1(b'blob '+str(len(inherited_bytes)).encode()+b'\0'+inherited_bytes).hexdigest()
    expected_inherited_blob_sha1='ac74b3812c826ad491fb829108f26397322e45eb'
    if inherited_blob_sha1 != expected_inherited_blob_sha1:
        raise RuntimeError('Inherited Original Hybrid source SHA changed; fail closed')
    from qqq_hybrid_profit_trend_replay_v1 import prepare_simulator_input
    adapted_spots_path=prepare_simulator_input(Path(args.spots_path))
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    variants=[
        ('NO_TAIL','NONE',0.0,args.friction_bps,False),
        ('LEGACY_NO_QQQ_DEBIT','NONE',0.0,args.friction_bps,True),
        ('ALWAYS_ON_2P','ALWAYS_ON',0.02,args.friction_bps,False),
        ('TRIGGERED_1P','TRIGGERED',0.01,args.friction_bps,False),
        ('TRIGGERED_2P','TRIGGERED',0.02,args.friction_bps,False),
        ('TRIGGERED_5P','TRIGGERED',0.05,args.friction_bps,False),
        ('TRIGGERED_2P_0BPS','TRIGGERED',0.02,0.0,False),
        ('TRIGGERED_2P_25BPS','TRIGGERED',0.02,25.0,False),
        ('TRIGGERED_2P_50BPS','TRIGGERED',0.02,50.0,False),
    ]
    rows=[];all_equities={}
    for label,mode,budget,bps,legacy_bug in variants:
        result=simulate(str(adapted_spots_path),False,args.tail_prices_path,mode,budget,bps,legacy_bug)
        cagr,maxdd,final_nav,opens,closes,events,e,tail_trades=result
        years=(e.date.iloc[-1]-e.date.iloc[0]).days/365.25
        tail_pnl=float(sum(float(t['net_pnl_usd'] or 0.0) for t in tail_trades))
        rows.append({
            'variant':label,'tail_mode':mode,'tail_budget_pct_nav_at_entry':budget,
            'tail_round_trip_friction_bps':bps,'start_date':str(e.date.iloc[0].date()),
            'end_date':str(e.date.iloc[-1].date()),'observations':int(len(e)),
            'elapsed_years':float(years),'initial_nav_usd':CAPITAL,'final_nav_usd':float(final_nav),
            'net_profit_usd':float(final_nav-CAPITAL),'cagr':float(cagr),
            'daily_mtm_maxdd':float(maxdd),'tail_trade_count':int(len(tail_trades)),
            'tail_closed_trade_count':int(sum(1 for t in tail_trades if t['status']=='CLOSED')),
            'tail_open_at_end':bool(any(t['status']=='MARKED_OPEN_AT_END' for t in tail_trades)),
            'tail_net_pnl_usd':tail_pnl,'tail_invested_days':int(e.tail_open.sum()),
            'max_tail_market_value_usd':float(e.tail_market_value.max()),
            'strategy_option_legs_opened':len(opens),'strategy_option_legs_closed':len(closes),
            'strategy_events':len(events)
        })
        all_equities[label]=e
        e.to_csv(out/f'{label.lower()}_equity.csv',index=False)
        pd.DataFrame(tail_trades).to_csv(out/f'{label.lower()}_tail_trades.csv',index=False)
    summary=pd.DataFrame(rows)
    summary.to_csv(out/'summary.csv',index=False)

    # Exact same base model over its full original window (untruncated by TAIL coverage).
    # This isolates whether the prior 13.70% headline depends on the QQQ cash-debit defect.
    full_window_rows=[]
    full_window_equities={}
    for label,legacy_bug in [
        ('FULL_WINDOW_CORRECTED_NO_TAIL',False),
        ('FULL_WINDOW_LEGACY_NO_QQQ_DEBIT',True),
    ]:
        fr=simulate(str(adapted_spots_path),False,None,'NONE',0.0,args.friction_bps,legacy_bug)
        fc,fdd,fn,fo,fx,fe,feq,ft=fr
        fyears=(feq.date.iloc[-1]-feq.date.iloc[0]).days/365.25
        full_window_rows.append({
            'variant':label,'start_date':str(feq.date.iloc[0].date()),
            'end_date':str(feq.date.iloc[-1].date()),'observations':int(len(feq)),
            'elapsed_years':float(fyears),'initial_nav_usd':CAPITAL,
            'final_nav_usd':float(fn),'net_profit_usd':float(fn-CAPITAL),
            'cagr':float(fc),'daily_mtm_maxdd':float(fdd),
            'accounting_bug_reproduced':bool(legacy_bug)
        })
        full_window_equities[label]=feq
        feq.to_csv(out/f'{label.lower()}_equity.csv',index=False)
    pd.DataFrame(full_window_rows).to_csv(out/'full_window_accounting_comparison.csv',index=False)
    annual=[]
    for label,e in all_equities.items():
        x=e.copy();x['year']=x.date.dt.year
        for year,g in x.groupby('year'):
            start_nav=float(g.nav.iloc[0]);end_nav=float(g.nav.iloc[-1])
            yr=max((g.date.iloc[-1]-g.date.iloc[0]).days/365.25,1/365.25)
            annual.append({
                'variant':label,'year':int(year),'first_date':str(g.date.iloc[0].date()),
                'last_date':str(g.date.iloc[-1].date()),'start_nav_usd':start_nav,
                'end_nav_usd':end_nav,'period_return':end_nav/start_nav-1,
                'annualized_period_return':(end_nav/start_nav)**(1/yr)-1 if end_nav>0 else -1,
                'period_maxdd':float((g.nav/g.nav.cummax()-1).min()),
                'trigger_days':int(g.tail_trigger.sum()),'tail_invested_days':int(g.tail_open.sum())
            })
    pd.DataFrame(annual).to_csv(out/'calendar_year.csv',index=False)
    report={
        'schema':'original-hybrid-tail-account-nav.v1','status':'COMPLETED',
        'strategy':'Original Hybrid BASELINE policy (dynamic deployment disabled); corrected account ledger for recommended arms; one isolated legacy-accounting-bug control for diagnosis',
        'accounting_audit':{
            'finding':'Inherited source includes a no-op expression cash_box[0]-row.qqq*n when opening QQQ core. Because it has no assignment operator, QQQ stock purchase cost is not deducted from cash in that original line.',
            'corrected_arms':'All arms except LEGACY_NO_QQQ_DEBIT debit QQQ stock purchases from cash before marking QQQ shares into NAV.',
            'legacy_control':'LEGACY_NO_QQQ_DEBIT deliberately preserves the missing cash debit to quantify the inherited error. It is diagnostic only and must not be treated as valid account performance.'
        },
        'evidence_class':'DERIVED_BS_VIX_MODEL_NOT_OPRA',
        'window':{'start':str(all_equities['NO_TAIL'].date.iloc[0].date()),
                  'end':str(all_equities['NO_TAIL'].date.iloc[-1].date()),
                  'observations':int(len(all_equities['NO_TAIL'])),
                  'elapsed_years':float((all_equities['NO_TAIL'].date.iloc[-1]-all_equities['NO_TAIL'].date.iloc[0]).days/365.25)},
        'input_sha256':{'spots_universe_json':sha256_file(args.spots_path),'adapted_spots':sha256_file(str(adapted_spots_path)),'tail_adjusted_close':sha256_file(args.tail_prices_path)},
        'inherited_strategy_source':{'path':'research/qqq_hybrid_dynamic_deployment_v1_1_replay.py','git_blob_sha1':inherited_blob_sha1,'expected_git_blob_sha1':expected_inherited_blob_sha1},
        'frozen_tail_rule':{
            'signal':'Previous close: abs VXX daily return >6%, or VIX >35, or proxy term slope <0, or QQQ daily return <-3%',
            'execution':'Next common trading session adjusted close; never same-close after signal',
            'entry':'Single open TAIL position; allocation is stated % of account NAV at entry; no overlapping TAIL cohorts',
            'exit':'After two consecutive non-triggering closes, exit on the next common session adjusted close',
            'reentry':'A later trigger can open a new TAIL position after the previous one has closed',
            'instrument':'TAIL ETF adjusted-close return proxy; no reconstructed bid/ask or historical executable share fill',
            'transaction_cost':'Round-trip bps split equally into entry/exit; 10 bps base, 0/25/50 bps sensitivity for 2% allocation',
            'funding':'TAIL purchase and sale flow through the same cash ledger; TAIL mark-to-market is included in total account NAV and subsequent NAV-based option sizing'
        },
        'limitations':[
            'Options use the inherited DERIVED_BS_VIX model and estimated spread haircuts, not historical OPRA chain quotes/fills.',
            'The VX term trigger remains the inherited VIX/MA20 proxy, not real historical VX futures M1/M2.',
            'TAIL adjusted close is a total-return proxy and not historical executable close/lot accounting.',
            'No broker commissions, margin, early assignment, forced liquidation or broker buying-power model is included.',
            'This is an in-sample experiment, not evidence of forward alpha.',
            'The inherited source has an identified QQQ cash-debit defect; only the explicit LEGACY_NO_QQQ_DEBIT row reproduces it. Use NO_TAIL and other corrected-account-ledger rows for the TAIL comparison.'
        ],
        'results':rows,
        'full_window_accounting_comparison':full_window_rows
    }
    (out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
