from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import broker_reconcile  # noqa: E402


def main() -> None:
    source = (ROOT / "broker_reconcile.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    called_names = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert "place_order" not in called_names
    assert "modify_order" not in called_names
    assert "cancel_order" not in called_names
    assert "unlock_trade" not in called_names

    parser = broker_reconcile.build_parser()
    args = parser.parse_args([
        "--input", "broker_import.json",
        "--acc-id", "123456",
        "--opening-cash", "50000",
    ])
    assert args.acc_id == 123456
    assert args.opening_cash == 50000.0

    assert broker_reconcile.canonical_symbol("US.QQQ") == "QQQ"
    assert broker_reconcile.canonical_symbol("QQQ") == "QQQ"
    assert broker_reconcile.position_side(0) == "LONG"
    assert broker_reconcile.position_side(1) == "SHORT"

    print("BROKER RECONCILIATION IMPORT CONTRACT TEST: PASS")


if __name__ == "__main__":
    main()
