# V2.3 Local Run → TXT → Grok

Grok 寫程式。你的 Windows 跑 Futu OpenD。TXT 是兩者之間的標準 API。

不要把 Futu 帳戶、密碼、Token、2FA 貼給 Grok。OpenD 已經登入即可。

---

## STEP 1

啟動 **Futu OpenD**。

## STEP 2

確認 OpenD **已登入**。監聽預設是 `127.0.0.1:11111`。

## STEP 3

在 repository 根目錄執行：

```bat
pip install futu-api
python -m backtest.local_diagnostic --diagnostic --futu-test
```

Windows 若 `python` 找不到，改用：

```bat
py -3 -m backtest.local_diagnostic --diagnostic --futu-test
```

或：

```bat
npm run diagnostic
```

## STEP 4

程式會寫出：

```
reports/local_run_result.txt
```

（同時有一份 `reports/local_run_result.json`，貼 TXT 即可。）

## STEP 5

把 `local_run_result.txt` **全部 COPY**。不要只貼最後幾行 console。

## STEP 6

貼回 Grok。Grok 會讀 PASS / FAIL / class（CODE / ENVIRONMENT / PERMISSION / DATA / API），然後給下一個最小修正，再請你用同一條 command 重跑。

---

## 這不是策略 FAIL

若 TXT 寫：

```
Futu OpenD = NOT CONNECTED
class: ENVIRONMENT
```

那是本機環境問題（OpenD 沒開、沒登入、port 不是 11111、沒裝 `futu-api`），**不是** V2.2 歷史回測被推翻。

Grok 的 Linux 預覽環境到不了你的 `127.0.0.1:11111`，所以預覽頁 `/live` 會停在 `WAITING_FOR_LOCAL_DIAGNOSTIC`。這是預期行為，不是假 LIVE。

---

## 不會做的事

- 不下真實單（沒有 `OpenSecTradeContext`）
- 不把缺失 IV 填成 0.25 再標 LIVE
- 不重寫 V2.2 歷史引擎
- 不要求你貼 source code
