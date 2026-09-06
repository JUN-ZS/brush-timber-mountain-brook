# brush-timber-mountain-brook

Relative-vol radar + QQQ/VXX backtest.

- **V2.2** Historical research engine (`/backtest`). Frozen. Do not retune to pass the gate.
- **V2.3** Futu OpenD live reality layer (`/live`) + local diagnostic TXT loop.

V2.3 does not replace V2.2. It asks a different question: *does a real QQQ option surface (IV, bid/ask, OI, Greeks) change what the Derived BS overlay concluded?* The code does not preset the answer.

## Local Futu diagnostic (Windows)

OpenD must already be logged in on the machine that runs this. Do not send credentials.

**STEP 1**  Start Futu OpenD.

**STEP 2**  Confirm login. Default listen: `127.0.0.1:11111`.

**STEP 3**  From the repo root:

```bat
python -m backtest.local_diagnostic --diagnostic --futu-test
```

**STEP 4**  The program writes `reports/local_run_result.txt`.

**STEP 5**  Copy the entire TXT.

**STEP 6**  Paste it back to Grok.

Full notes: [LOCAL_RUN.md](LOCAL_RUN.md).

Optional SDK (Windows only):

```bat
pip install -r requirements-futu.txt
```

Tests do **not** require `futu-api` or OpenD.

## Tests

```bat
npm test
python -m unittest discover -s backtest/tests -p "test_*.py"
```

## Layout

```
src/lib/pulse/          V2.2 historical engine (untouched by V2.3 research)
src/lib/pulse/live.ts   Browser live layer (UNAVAILABLE in preview)
src/routes/live.tsx     LIVE / PAPER UI
backtest/               Python OpenD adapter + diagnostic
reports/                TXT/JSON written locally, not committed
```
