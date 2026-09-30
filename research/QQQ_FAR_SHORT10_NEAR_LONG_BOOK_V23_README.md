# QQQ V23 Far-Short / Near-Long Book

Research only. Not a live signal. Isolated from V22.

User sentence: N+10 SHORT CALL 做遠月, 不斷策略式堆和放收各種近月 LONG.

Frozen contract
- Gate: close/52w >= 0.98 AND ext200 >= 8%.
- Short: always N=10, 60-120 DTE, FOTM delta in {1,2,5,8,10}.
- Long book: two near ATM buckets, 1 each — A 18-25 DTE, B 25-35 DTE.
- 堆: on a new far-short cycle, buy any empty near bucket.
- 放/轉: if a near long has remaining DTE < 7 on a signal day, sell bid and replace in the same bucket.
- Cycle exit: far short strike touched OR 30d. Close the 10 far shorts only. Near longs stay unless rolled.
- Dollar WIN = cycle cash P&L > 0. Geo WIN = far short never touched.
