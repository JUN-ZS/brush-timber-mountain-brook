from __future__ import annotations

import os


def enum_name(value):
    """Normalize Futu enum/string representations to their terminal name."""
    return str(value or "").strip().upper().split(".")[-1]


class FutuTradeReader:
    """Read-only trade/account observer with an explicit Futu account ID."""

    def __init__(self, host="127.0.0.1", port=11111, real=True, acc_id=None):
        self.host = host
        self.port = port
        self.real = bool(real)
        raw = acc_id if acc_id is not None else os.getenv("FUTU_ACC_ID")
        try:
            self.acc_id = int(str(raw).strip()) if raw is not None and str(raw).strip() else None
        except (TypeError, ValueError):
            self.acc_id = None
        self.ctx = None
        self.futu = None
        self.account = None
        self.account_error = None

    @staticmethod
    def _cell(row, *names):
        for name in names:
            try:
                value = row.get(name)
            except Exception:
                try:
                    value = row[name]
                except Exception:
                    value = None
            if value is not None:
                return value
        return None

    @classmethod
    def _account_rows(cls, data):
        if hasattr(data, "iterrows"):
            for _, row in data.iterrows():
                yield {str(k): row[k] for k in data.columns}
        elif isinstance(data, list):
            for row in data:
                if isinstance(row, dict):
                    yield row

    def _verify_account(self):
        if self.acc_id is None or self.acc_id <= 0:
            self.account_error = "FUTU_ACC_ID_REQUIRED"
            return False

        ret, data = self.ctx.get_acc_list()
        if ret != self.futu.RET_OK:
            self.account_error = "get_acc_list: " + str(data)
            return False

        candidates = []
        requested_env = self.futu.TrdEnv.REAL if self.real else self.futu.TrdEnv.SIMULATE
        for row in self._account_rows(data):
            try:
                row_id = int(self._cell(row, "acc_id", "accID"))
            except (TypeError, ValueError):
                continue

            raw_env = self._cell(row, "trd_env", "trdEnv")
            env = enum_name(raw_env)
            status = enum_name(self._cell(row, "acc_status", "accStatus"))

            # Keep the raw row for evidence, but validate the requested account
            # and trading environment before any position/order/deal query.
            if row_id == self.acc_id:
                candidates.append((row, env, status))

        if not candidates:
            self.account_error = f"FUTU_ACC_ID_NOT_FOUND:{self.acc_id}"
            return False

        row, env, status = candidates[0]
        expected_env = enum_name(requested_env)
        if env != expected_env:
            self.account_error = (
                f"FUTU_ACC_ENV_MISMATCH:{self.acc_id}:expected={expected_env}:actual={env or 'MISSING'}"
            )
            return False
        if status != "ACTIVE":
            self.account_error = f"FUTU_ACC_NOT_ACTIVE:{self.acc_id}:{status or 'MISSING'}"
            return False

        auth = self._cell(row, "trdmarket_auth", "trdMarketAuthList")
        auth_text = str(auth or "").upper()
        if "US" not in auth_text:
            self.account_error = f"FUTU_ACC_NO_US_AUTH:{self.acc_id}"
            return False

        self.account = {
            "acc_id": self.acc_id,
            "trd_env": env or expected_env,
            "acc_status": status or "UNKNOWN",
            "card_num_last4": str(self._cell(row, "card_num", "cardNum") or "")[-4:],
            "uni_card_num_last4": str(self._cell(row, "uni_card_num", "uniCardNum") or "")[-4:],
            "trdmarket_auth": auth,
        }
        return True

    def connect(self):
        import futu
        self.futu = futu
        if self.acc_id is None or self.acc_id <= 0:
            raise RuntimeError("FUTU_ACC_ID_REQUIRED")
        self.ctx = futu.OpenSecTradeContext(
            host=self.host,
            port=self.port,
            filter_trdmarket=futu.TrdMarket.US,
        )
        if not self._verify_account():
            self.close()
            raise RuntimeError(self.account_error or "FUTU_ACCOUNT_SELECTION_BLOCKED")

    def close(self):
        if self.ctx:
            try:
                self.ctx.close()
            except Exception:
                pass
            self.ctx = None

    @staticmethod
    def _position_side(raw):
        if isinstance(raw, bool):
            return "UNKNOWN"
        if isinstance(raw, (int, float)):
            return {0: "LONG", 1: "SHORT"}.get(int(raw), "UNKNOWN")
        s = str(raw or "").strip().upper()
        if s in {"LONG", "LONG_POSITION", "POSITION_SIDE_LONG", "POSITION_SIDE_LONG()", "BUY", "0"}:
            return "LONG"
        if s in {"SHORT", "SHORT_POSITION", "POSITION_SIDE_SHORT", "POSITION_SIDE_SHORT()", "SELL", "1"}:
            return "SHORT"
        return "UNKNOWN"

    @staticmethod
    def _trade_side(raw):
        if isinstance(raw, bool):
            return "UNKNOWN"
        if isinstance(raw, (int, float)):
            return {1: "BUY", 2: "SELL", 3: "SELL_SHORT", 4: "BUY_BACK"}.get(int(raw), "UNKNOWN")
        s = str(raw or "").strip().upper()
        if s in {"BUY", "TRD_SIDE_BUY", "1"}:
            return "BUY"
        if s in {"SELL", "TRD_SIDE_SELL", "2"}:
            return "SELL"
        if s in {"SELL_SHORT", "TRD_SIDE_SELLSHORT", "3"}:
            return "SELL_SHORT"
        if s in {"BUY_BACK", "TRD_SIDE_BUYBACK", "4"}:
            return "BUY_BACK"
        return "UNKNOWN"

    @staticmethod
    def _avg_cost(row):
        for key in ("average_cost", "average_cost_price", "diluted_cost",
                    "diluted_cost_price", "cost_price"):
            try:
                value = float(row.get(key) or 0)
            except Exception:
                value = 0
            if value > 0:
                return value
        return 0.0

    def _parse_deals(self, deal_df):
        deals = []
        if hasattr(deal_df, "iterrows"):
            for _, row in deal_df.iterrows():
                deals.append({
                    "deal_id": str(row.get("deal_id", row.get("dealID", row.get("orderIDEx", "")))),
                    "code": str(row.get("code", "")),
                    "side": self._trade_side(row.get("trd_side", row.get("trdSide", ""))),
                    "raw_side": str(row.get("trd_side", row.get("trdSide", "")) or ""),
                    "qty": int(float(row.get("qty", 0) or 0)),
                    "price": float(row.get("price", 0) or 0),
                    "created_at": str(row.get("create_time", row.get("createTime", "")) or ""),
                })
        return deals

    def read(self, history_start=None, history_end=None):
        self.connect()
        try:
            env = self.futu.TrdEnv.REAL if self.real else self.futu.TrdEnv.SIMULATE

            ret, pos = self.ctx.position_list_query(
                position_market=self.futu.TrdMarket.US,
                trd_env=env,
                acc_id=self.acc_id,
            )
            if ret != self.futu.RET_OK:
                raise RuntimeError("position_list_query: " + str(pos))

            ret2, orders = self.ctx.order_list_query(
                order_market=self.futu.TrdMarket.US,
                trd_env=env,
                acc_id=self.acc_id,
            )
            if ret2 != self.futu.RET_OK:
                raise RuntimeError("order_list_query: " + str(orders))

            ps = []
            if hasattr(pos, "iterrows"):
                for _, row in pos.iterrows():
                    raw_side = row.get("position_side", row.get("positionSide", ""))
                    side = self._position_side(raw_side)
                    qty = int(float(row.get("qty", 0) or 0))
                    if qty:
                        ps.append({
                            "code": str(row.get("code", "")),
                            "side": side,
                            "qty": qty,
                            "avg_cost": self._avg_cost(row),
                            "raw_position_side": str(raw_side if raw_side is not None else ""),
                        })

            os = []
            if hasattr(orders, "iterrows"):
                for _, row in orders.iterrows():
                    os.append({
                        "order_id": str(row.get("order_id", "")),
                        "code": str(row.get("code", "")),
                        "side": self._trade_side(row.get("trd_side", "")),
                        "raw_side": str(row.get("trd_side", "") or ""),
                        "qty": int(float(row.get("qty", 0) or 0)),
                        "price": float(row.get("price", 0) or 0),
                        "status": str(row.get("order_status", "")).upper(),
                        "created_at": str(row.get("create_time", "") or ""),
                        "updated_at": str(row.get("updated_time", row.get("create_time", "")) or ""),
                        "dealt_qty": int(float(row.get("dealt_qty", 0) or 0)),
                        "dealt_avg_price": float(row.get("dealt_avg_price", 0) or 0) or None,
                        "remark": str(row.get("remark", "") or ""),
                    })

            deals = []
            deal_warning = None
            history_used = False
            try:
                if hasattr(self.ctx, "deal_list_query"):
                    ret3, deal_df = self.ctx.deal_list_query(
                        deal_market=self.futu.TrdMarket.US,
                        trd_env=env,
                        acc_id=self.acc_id,
                    )
                    if ret3 == self.futu.RET_OK:
                        deals.extend(self._parse_deals(deal_df))
                    else:
                        deal_warning = str(deal_df)
                else:
                    deal_warning = "deal_list_query unavailable in installed futu package"
            except Exception as exc:
                deal_warning = repr(exc)

            if history_start and self.real and hasattr(self.ctx, "history_deal_list_query"):
                try:
                    start = str(history_start)[:10]
                    end = str(history_end or "")[:10]
                    if not end:
                        from datetime import date
                        end = date.today().isoformat()
                    ret4, hist_df = self.ctx.history_deal_list_query(
                        deal_market=self.futu.TrdMarket.US,
                        start=start,
                        end=end,
                        trd_env=env,
                        acc_id=self.acc_id,
                    )
                    if ret4 == self.futu.RET_OK:
                        history_used = True
                        by_id = {str(d.get("deal_id")): d for d in deals if d.get("deal_id")}
                        for d in self._parse_deals(hist_df):
                            did = str(d.get("deal_id", ""))
                            if did and did not in by_id:
                                by_id[did] = d
                        deals = list(by_id.values())
                    else:
                        deal_warning = (deal_warning + " | " if deal_warning else "") + "history_deal_list_query: " + str(hist_df)
                except Exception as exc:
                    deal_warning = (deal_warning + " | " if deal_warning else "") + "history_deal_list_query: " + repr(exc)
            elif history_start and self.real:
                deal_warning = (deal_warning + " | " if deal_warning else "") + "history_deal_list_query unavailable in installed futu package"

            return {
                "source": "FUTU_TRADE_READ_ONLY",
                "account": self.account,
                "positions": ps,
                "orders": os,
                "deals": deals,
                "history_backfill_used": history_used,
                "history_start": str(history_start) if history_start else None,
                "history_end": str(history_end) if history_end else None,
                "deal_warning": deal_warning,
            }
        finally:
            self.close()
