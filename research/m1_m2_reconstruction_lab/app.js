const $ = id => document.getElementById(id);
const L = window.M1M2Lab;

const S = {
  rows: [],
  recon: [],
  comparison: null,
  masked: true,
  idx: 0,
  method: "ARCHIVE_V4_PROXY"
};

const fmt = (x, d = 2) => Number.isFinite(x) ? x.toFixed(d) : "—";
const pct = (x, d = 2) => Number.isFinite(x) ? (x * 100).toFixed(d) + "%" : "—";

function parseCSV(text) {
  const lines = text.trim().split(/\r?\n/);
  const head = lines.shift().split(",");
  return lines.filter(Boolean).map(line => {
    const parts = line.split(",");
    const r = {};
    head.forEach((h, i) => r[h] = parts[i] ?? "");
    return r;
  });
}

function load() {
  fetch("../data/vx_m1_m2_external_2016_2022.csv", { cache: "no-store" })
    .then(r => { if (!r.ok) throw new Error("CSV HTTP " + r.status); return r.text(); })
    .then(text => {
      S.rows = parseCSV(text);
      S.recon = L.reconstructSeries(L.buildMaskedInput(S.rows), S.method);
      S.comparison = L.compare(S.rows, S.recon);
      $("range").max = Math.max(0, S.rows.length - 1);
      $("range").value = 0;
      const audit = L.leakageAudit(S.rows, S.method);
      renderAll(audit);
      window.addEventListener("resize", draw);
    })
    .catch(err => {
      $("dataBadge").textContent = "LOAD ERROR";
      $("dataBadge").className = "badge warn";
      $("methodBox").textContent = "Cannot load local CSV: " + err.message;
    });
}

function renderAll(audit) {
  const m = S.comparison.metrics;
  $("dataBadge").textContent = "EXTERNAL OBSERVED · UNVALIDATED";
  $("dataBadge").className = "badge warn";
  $("rowsValue").textContent = m.n.toLocaleString();
  $("coverage").textContent = S.rows[0]?.Date + " → " + S.rows[S.rows.length - 1]?.Date;
  $("methodValue").textContent = S.method;
  $("signValue").textContent = pct(m.termSignAgreementPct / 100);
  $("regimeValue").textContent = pct(m.regimeAgreementPct / 100);
  $("actionValue").textContent = pct(m.actionAgreementPct / 100);
  $("leakageValue").textContent = audit.pass ? "PASS" : "FAIL";
  $("methodBox").innerHTML =
    "<b>" + L.METHODS[S.method].label + "</b><br>" +
    L.METHODS[S.method].description + "<br><br>" +
    "M1/M2 truth = evaluation-only; reconstructed values are DERIVED and UNVALIDATED.";
  $("m1mae").textContent = fmt(m.m1.mae);
  $("m1rmse").textContent = fmt(m.m1.rmse);
  $("m1mape").textContent = Number.isFinite(m.m1.mapePct) ? m.m1.mapePct.toFixed(2) + "%" : "—";
  $("m2mae").textContent = fmt(m.m2.mae);
  $("m2rmse").textContent = fmt(m.m2.rmse);
  $("m2mape").textContent = Number.isFinite(m.m2.mapePct) ? m.m2.mapePct.toFixed(2) + "%" : "—";
  $("smae").textContent = pct(m.s.mae);
  $("srmse").textContent = pct(m.s.rmse);
  $("sbias").textContent = pct(m.s.bias);
  $("integrityBanner").innerHTML =
    "<b>MASK TEST:</b> " + (S.masked ? "M1/M2 hidden from the reconstruction path." : "M1/M2 display restored for inspection.") +
    " The evaluation object remains separate; the reconstruction receives only VIX history.";
  $("range").oninput = () => { S.idx = Number($("range").value); renderSelected(); draw(); };
  $("maskBtn").onclick = () => { S.masked = !S.masked; renderSelected(); };
  $("exportBtn").onclick = exportCsv;
  renderWorst();
  renderSelected();
  draw();
}

function renderSelected() {
  const x = S.comparison?.rows[S.idx];
  if (!x) return;
  $("selDate").textContent = x.date;
  $("selVix").textContent = fmt(x.vix);
  $("selM1").textContent = S.masked ? "[MASKED] / " + fmt(x.reconstructed.m1) : fmt(x.truth.m1) + " / " + fmt(x.reconstructed.m1);
  $("selM2").textContent = S.masked ? "[MASKED] / " + fmt(x.reconstructed.m2) : fmt(x.truth.m2) + " / " + fmt(x.reconstructed.m2);
  $("selS").textContent = S.masked ? "[MASKED] / " + pct(x.reconstructed.s) : pct(x.truth.s) + " / " + pct(x.reconstructed.s);
  $("selRegime").textContent = x.truth.regime + " / " + x.reconstructed.regime;
  $("selAction").textContent = x.truth.action + " / " + x.reconstructed.action;
  $("selMatch").textContent = "REGIME " + (x.regimeMatch ? "✓" : "✕") + " · ACTION " + (x.actionMatch ? "✓" : "✕");
  $("cursorDate").textContent = x.date;
}

function renderWorst() {
  const rows = [
    ...L.topErrors(S.comparison, "m1", 5).map(x => ({ type: "M1", row: x, err: x.errors.m1 })),
    ...L.topErrors(S.comparison, "m2", 5).map(x => ({ type: "M2", row: x, err: x.errors.m2 })),
    ...L.topErrors(S.comparison, "s", 5).map(x => ({ type: "S", row: x, err: x.errors.s }))
  ].sort((a, b) => Math.abs(b.err) - Math.abs(a.err)).slice(0, 12);

  $("worstRows").innerHTML = rows.map(x =>
    "<div class='worst-row'>" +
      "<div><b>" + x.type + "</b><small>" + x.row.date + "</small></div>" +
      "<div>VIX " + fmt(x.row.vix) + "</div>" +
      "<div>ERR " + (x.type === "S" ? pct(x.err) : fmt(x.err)) + "</div>" +
      "<div>" + x.row.truth.regime + " → " + x.row.reconstructed.regime + "</div>" +
    "</div>"
  ).join("");
}

function draw() {
  const c = $("chart");
  const rect = c.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  const w = Math.max(700, rect.width);
  const h = 340;
  c.width = w * dpr; c.height = h * dpr;
  const ctx = c.getContext("2d");
  ctx.setTransform(dpr,0,0,dpr,0,0);
  ctx.clearRect(0,0,w,h);
  ctx.fillStyle = "#090e14"; ctx.fillRect(0,0,w,h);

  const seriesA = S.comparison.rows.map(x => x.truth.s * 100);
  const seriesB = S.comparison.rows.map(x => x.reconstructed.s * 100);
  const vals = seriesA.concat(seriesB).filter(Number.isFinite);
  if (!vals.length) return;
  let lo = Math.min(...vals), hi = Math.max(...vals);
  if (lo === hi) { lo -= 1; hi += 1; }
  const pad = 25;
  const x = i => pad + (w - pad*2) * (i / Math.max(1, seriesA.length - 1));
  const y = v => h - pad - (h - pad*2) * ((v - lo) / (hi - lo));

  ctx.strokeStyle = "#26313d"; ctx.lineWidth = 1;
  for (let k = 0; k < 5; k++) {
    const yy = pad + (h - pad*2) * k / 4;
    ctx.beginPath(); ctx.moveTo(pad,yy); ctx.lineTo(w-pad,yy); ctx.stroke();
  }
  const yz = y(0);
  ctx.strokeStyle = "#626d7b"; ctx.setLineDash([4,4]);
  ctx.beginPath(); ctx.moveTo(pad,yz); ctx.lineTo(w-pad,yz); ctx.stroke(); ctx.setLineDash([]);

  function line(series, stroke) {
    ctx.strokeStyle = stroke; ctx.lineWidth = 1.5; ctx.beginPath();
    let started = false;
    series.forEach((v,i) => {
      if (!Number.isFinite(v)) { started = false; return; }
      if (!started) { ctx.moveTo(x(i),y(v)); started = true; }
      else ctx.lineTo(x(i),y(v));
    });
    ctx.stroke();
  }
  line(seriesA, "#b9c2cc");
  line(seriesB, "#7184a2");

  S.comparison.rows.forEach((r,i) => {
    if (!r.actionMatch) {
      const v = r.truth.s * 100;
      if (Number.isFinite(v)) {
        ctx.fillStyle = "#d06b5f";
        ctx.beginPath(); ctx.arc(x(i),y(v),2.2,0,Math.PI*2); ctx.fill();
      }
    }
  });

  const cx = x(S.idx);
  ctx.strokeStyle = "#e6edf5"; ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(cx,pad); ctx.lineTo(cx,h-pad); ctx.stroke();

  ctx.fillStyle = "#7d8998"; ctx.font = "10px system-ui";
  ctx.fillText(hi.toFixed(1) + "%", 4, y(hi)+3);
  ctx.fillText("0%", 4, yz+3);
  ctx.fillText(lo.toFixed(1) + "%", 4, y(lo)+3);
  $("startDate").textContent = S.rows[0]?.Date || "—";
  $("endDate").textContent = S.rows[S.rows.length-1]?.Date || "—";
}

function exportCsv() {
  if (!S.comparison) return;
  const blob = new Blob([L.csvFromComparison(S.comparison)], {type:"text/csv;charset=utf-8"});
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = "m1_m2_mask_reconstruction_results.csv";
  a.click(); URL.revokeObjectURL(url);
}

load();
