# QQQ V22 Near-Short / Far-Long Book

Research only. Not a live signal. Isolated branch.

User sentence: N+10 SHORT CALL 做近月, 不斷策略式堆和放收各種遠月 LONG.

Frozen contract
- Gate: close/52w >= 0.98 AND ext200 >= 8% (same extreme-high net).
- Short: always N=10, 18-35 DTE, FOTM target delta in {1,2,5,8,10}.
- Long book: two buckets, 1 contract each — A 60-90 DTE ATM, B 90-120 DTE ATM.
- 堆: on a new short cycle, buy any empty bucket.
- 轉/放: if a long has remaining DTE < 40 on a signal day, sell bid and replace in the same bucket.
- Cycle exit: near short strike touched OR 30d OR near expiry. Close the 10 shorts only. Longs stay unless rolled.
- End of sample: mark remaining longs at last bid.
- Dollar WIN = cycle cash P&L > 0 (short close + any long roll that day).
- Geo WIN = near short never touched in the hold.
