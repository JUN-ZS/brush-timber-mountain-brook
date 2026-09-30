from __future__ import annotations


class FutuTradeReader:
    """Read-only Futu US account reconciliation. Never unlocks or submits orders."""

    def __init__(self, host="127.0.0.1", port=11111, real=True):
        self.host = host
        self.port = port
        self.real = real
        self.ctx = None
        self.futu = None

    def connect(self):
        import futu

        self.futu = futu
        self.ctx = futu.OpenSecTradeContext(
            host=self.host,
            port=self.port,
            filter_trdmarket=futu.TrdMarket.US,
        )

    def close(self):
        if self.ctx:
            try:
                self.ctx.close()
            except Exception:
                pass
            self.ctx = None

    @staticmethod
    def _position_side(raw: object) -> str:
        s = str(raw or "").strip().upper()
        if s in {"LONG", "LONG_POSITION", "BUY"}:
            return "LONG"
        if s in {"SHORT", "SHORT_POSITION", "SELL"}:
            return "SHORT"
        return "UNKNOWN"

    def read(self):
        self.connect()
        try:
            env = self.futu.TrdEnv.REAL if self.real else self.futu.TrdEnv.SIMULATE

            ret, pos = self.ctx.position_list_query(
                position_market=self.futu.TrdMarket.US,
                trd_env=env,
            )
            if ret != self.futu.RET_OK:
                raise RuntimeError("position_list_query: " + str(pos))

            ret2, orders = self.ctx.order_list_query(
                order_market=self.futu.TrdMarket.US,
                trd_env=env,
            )
            if ret2 != self.futu.RET_OK:
                raise RuntimeError("order_list_query: " + str(orders))

            ps = []
            if hasattr(pos, "iterrows"):
                for _, row in pos.iterrows():
                    side = self._position_side(
                        row.get("position_side", row.get("positionSide", ""))
                    )
                    qty = int(float(row.get("qty", 0) or 0))
                    if not qty:
                        continue
                    ps.append(
                        {
                            "code": str(row.get("code", "")),
                            "side": side,
                            "qty": qty,
                            "avg_cost": float(
                                row.get(
                                    "average_cost_price",
                                    row.get("cost_price", 0),
                                )
                                or 0
                            ),
                            "raw_position_side": str(
                                row.get("position_side", row.get("positionSide", ""))
                                or ""
                            ),
                        }
                    )

            os = []
            if hasattr(orders, "iterrows"):
                for _, row in orders.iterrows():
                    os.append(
                        {
                            "order_id": str(row.get("order_id", "")),
                            "code": str(row.get("code", "")),
                            "side": str(row.get("trd_side", "")).upper(),
                            "qty": int(float(row.get("qty", 0) or 0)),
                            "price": float(row.get("price", 0) or 0),
                            "status": str(row.get("order_status", "")).upper(),
                            "created_at": str(row.get("create_time", "") or ""),
                            "updated_at": str(
                                row.get("updated_time", row.get("create_time", "")) or ""
                            ),
                            "dealt_qty": int(float(row.get("dealt_qty", 0) or 0)),
                            "dealt_avg_price": float(
                                row.get("dealt_avg_price", 0) or 0
                            )
                            or None,
                            "remark": str(row.get("remark", "") or ""),
                        }
                    )

            deals = []
            deal_warning = None
            try:
                if hasattr(self.ctx, "deal_list_query"):
                    ret3, deal_df = self.ctx.deal_list_query(
                        deal_market=self.futu.TrdMarket.US,
                        trd_env=env,
                    )
                    if ret3 == self.futu.RET_OK and hasattr(deal_df, "iterrows"):
                        for _, row in deal_df.iterrows():
                            deals.append(
                                {
                                    "deal_id": str(
                                        row.get("deal_id", row.get("dealID", ""))
                                    ),
                                    "code": str(row.get("code", "")),
                                    "side": str(
                                        row.get("trd_side", row.get("trdSide", ""))
                                    ).upper(),
                                    "qty": int(float(row.get("qty", 0) or 0)),
                                    "price": float(row.get("price", 0) or 0),
                                    "created_at": str(
                                        row.get(
                                            "create_time",
                                            row.get("createTime", ""),
                                        )
                                        or ""
                                    ),
                                }
                            )
                    elif ret3 != self.futu.RET_OK:
                        deal_warning = str(deal_df)
                else:
                    deal_warning = "deal_list_query unavailable in installed futu package"
            except Exception as exc:
                deal_warning = repr(exc)

            return {
                "source": "FUTU_TRADE_READ_ONLY",
                "positions": ps,
                "orders": os,
                "deals": deals,
                "deal_warning": deal_warning,
            }
        finally:
            self.close()
