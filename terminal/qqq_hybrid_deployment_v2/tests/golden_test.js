import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import assert from 'node:assert';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
globalThis.window = {};
vm.runInThisContext(fs.readFileSync(path.join(__dirname, '..', 'engine.js'), 'utf8'));
const E = globalThis.window.HybridEngine;

function run(label, data, expected) {
  const a = E.derive(data);
  const b = E.derive(data);
  assert.deepStrictEqual(a, b, `${label}: non-deterministic`);
  for (const [k, v] of Object.entries(expected)) assert.strictEqual(a[k], v, `${label}: ${k}`);
}

run('BLOCK M1/M2 missing', {qqq:756,vxx:17.2,vix:15.4,s:null}, {state:'DATA INCOMPLETE',action:'HOLD',blocked:true});
run('CARRY', {qqq:756,vxx:17.2,vix:15.4,s:8}, {state:'CARRY',action:'BUY',blocked:false,vxxTarget:18});
run('WEAKENING', {qqq:756,vxx:17.2,vix:18,s:3}, {state:'WEAKENING',action:'HOLD',blocked:false,vxxTarget:18});
run('PRE-SHOCK backwardation', {qqq:756,vxx:20,vix:20,s:-1}, {state:'PRE-SHOCK',action:'REDUCE',blocked:false,vxxTarget:0,vxxCalls:0});
run('SHOCK', {qqq:720,vxx:24,vix:32,s:-4}, {state:'SHOCK',action:'REDUCE',blocked:false,vxxTarget:0,vxxCalls:0});
console.log('Golden engine behavior PASS');
