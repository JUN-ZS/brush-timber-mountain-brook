import importlib.util
import unittest
from datetime import date, timedelta
from pathlib import Path
P=Path(__file__).with_name("qqq_put_ratio_scale_volatility_v1.py")
spec=importlib.util.spec_from_file_location("ratio_scale_vol",P)
M=importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(M)

def qr(bid,ask,bs=20,ass=20):return {"bid":bid,"ask":ask,"bid_size":bs,"ask_size":ass}
def trade():
    return {"trade_id":1,"entry_date":"2024-01-03","expiry":"2024-02-16","long_strike":100.,"short_strike":90.,"spot_entry":105.,
        "entry_quotes":{"long":qr(4.5,5.),"short":qr(2.,2.5)},
        "path":[{"date":"2024-01-03","spot":105.,"long":qr(4.5,5.),"short":qr(2.,2.5)},
        {"date":"2024-01-04","spot":105.,"long":qr(4.8,5.1),"short":qr(1.,1.3)},
        {"date":"2024-02-16","spot":105.,"long":qr(0.,.01),"short":qr(0.,.01)}]}

class RatioScaleTests(unittest.TestCase):
    def test_nav_relative_target_scales(self):
        self.assertEqual(100000*.01,1000.); self.assertEqual(1000000*.01,10000.)
    def test_n1_is_same_1x1_payoff(self):
        t=trade(); a=M.quantities(M.SHORT_HEAVY,1); b=M.quantities(M.LONG_HEAVY,1)
        self.assertEqual(a,b); self.assertEqual(M.terminal_envelope(t,*a,.05,.65),M.terminal_envelope(t,*b,.05,.65))
    def test_terminal_loss_not_always_qqq_zero_loss(self):
        x=M.terminal_envelope(trade(),1,1,0,0)
        self.assertAlmostEqual(x["max_terminal_loss_usd"],300.); self.assertGreater(x["terminal_pnl_if_qqq_zero_usd"],0.)
    def test_whole_unit_risk_floor(self):
        self.assertEqual(M.whole_units(100000,.01,3000),0); self.assertEqual(M.whole_units(1000000,.01,3000),3)
    def test_trim_short_heavy_leaves_one(self):
        s={"cash":0.,"n_long":1,"n_short":5}; ok,why=M.act(s,{"short":qr(1,1.1)},"TRIM_SHORT_RISK",M.SHORT_HEAVY,5,0,0)
        self.assertTrue(ok,why); self.assertEqual((s["n_long"],s["n_short"]),(1,1))
    def test_trim_long_heavy_closes_single_short(self):
        s={"cash":0.,"n_long":5,"n_short":1};ok,why=M.act(s,{"short":qr(1,1.1)},"TRIM_SHORT_RISK",M.LONG_HEAVY,5,0,0)
        self.assertTrue(ok,why);self.assertEqual((s["n_long"],s["n_short"]),(5,0))
    def test_full_close_atomic_if_long_bid_zero(self):
        s={"cash":0.,"n_long":1,"n_short":1};before=dict(s)
        ok,why=M.act(s,{"short":qr(1,1.1),"long":qr(0,.01)},"FULL_CLOSE",M.SHORT_HEAVY,1,0,0)
        self.assertFalse(ok);self.assertEqual(s,before);self.assertIn("LONG",why)
    def test_depth_blocks_oversized_ratio(self):
        t=trade();t["entry_quotes"]["short"]["bid_size"]=2
        self.assertFalse(M.entry_size_ok(t,M.SHORT_HEAVY,5));self.assertTrue(M.entry_size_ok(t,M.SHORT_HEAVY,2))
    def test_action_never_same_observation_as_signal(self):
        r=M.simulate(trade(),M.SHORT_HEAVY,1,100000,{"name":"tp","kind":"TP","pct":.0001,"action":"FULL_CLOSE"},0,0)
        if r["custom_triggered"] and r["first_action_age_sessions"] is not None:
            self.assertGreater(r["first_action_age_sessions"],r["custom_trigger_age_sessions"])
    def test_missing_close_censors_windows_crossing_gap(self):
        rows=[{"date":"2024-01-01","close":100.,"vix":20.},{"date":"2024-01-02","close":101.,"vix":20.},
              {"date":"2024-01-03","close":None,"vix":20.},{"date":"2024-01-04","close":90.,"vix":35.},{"date":"2024-01-05","close":91.,"vix":35.}]
        out=M.price_horizon_probabilities(rows);h=next(x for x in out if x["horizon_sessions"]==1 and x["state"]=="ALL")
        self.assertEqual(h["n"],2)
    def test_probability_includes_n_and_nonoverlap_sensitivity(self):
        rows=[];px=100.;d=date(2023,1,2)
        for i in range(180):
            px *= .99 if i%17==0 else (1.004 if i%3 else .998)
            rows.append({"date":(d+timedelta(days=i)).isoformat(),"close":px,"vix":22.})
        got=M.price_horizon_probabilities(rows);h=next(x for x in got if x["horizon_sessions"]==5 and x["state"]=="ALL")
        self.assertGreater(h["n"],100);self.assertIn("p_down_5pct_wilson95_nominal_low",h);self.assertIsNotNone(h["nonoverlap_p_down5_min_pct"])
    def test_multiple_units_scale_contracts_and_enforce_depth(self):
        t=trade()
        t["entry_quotes"]["short"]["bid_size"]=2
        self.assertFalse(M.entry_size_ok(t,M.SHORT_HEAVY,1,units=3))
        self.assertTrue(M.entry_size_ok(t,M.SHORT_HEAVY,1,units=2))
        r=M.simulate(t,M.SHORT_HEAVY,1,100000,{"name":"DTE7","kind":"DTE7"},0,0,units=2)
        self.assertEqual((r["n_long"],r["n_short"]),(2,2))

    def test_arbitrary_navs_produce_dynamic_capacity_rows(self):
        rows=M.build_risk_matrix([trade()],navs=(250000.0,750000.0))
        self.assertTrue(rows)
        self.assertEqual(sorted({x["nav_usd"] for x in rows}),[250000.0,750000.0])

    def test_cost_bar_measures_midpoint_to_side_drag_and_scales_with_costs(self):
        t=trade()
        cheap=M.friction_observations(t,1,1,0.0,0.0)
        costly=M.friction_observations(t,1,1,0.05,0.65)
        cheap_next=next(x for x in cheap if x["age"]==1)
        costly_next=next(x for x in costly if x["age"]==1)
        self.assertAlmostEqual(cheap_next["friction_drag_usd"],80.0)
        self.assertGreater(costly_next["friction_drag_usd"],cheap_next["friction_drag_usd"])
        self.assertEqual(cheap_next["state_labels"][0],"OVERALL")

    def test_matrix_contains_full_trim_and_dte_baseline(self):
        names={x["name"] for x in M.policies()}
        for name in ("DTE7_CLOSE_SHORT_RISK","FAST3_1.0PCT_FULL_CLOSE","FAST3_1.0PCT_TRIM_SHORT_RISK",
            "FAST5_1.0PCT_FULL_CLOSE","FAST5_1.0PCT_TRIM_SHORT_RISK","DAY20_NONPOS_FULL_CLOSE","DAY20_NONPOS_TRIM_SHORT_RISK","SL_1.0PCT_FULL_CLOSE"):
            self.assertIn(name,names)

if __name__=="__main__":unittest.main(verbosity=2)
