
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from providers.cboe_delayed_vx import _date, STANDARD

assert STANDARD.fullmatch("VX/V6")
assert STANDARD.fullmatch("VX/X6")
assert not STANDARD.fullmatch("VX40/V6")
assert not STANDARD.fullmatch("VXT/V6")
assert _date("10/21/2026").isoformat()=="2026-10-21"
print("Cboe provider filter PASS")
