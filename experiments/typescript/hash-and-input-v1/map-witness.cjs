/* Untimed diagnostic: observe the unchanged emitted application's seven Maps. */
"use strict";
const fs = require("node:fs");
const path = require("node:path");
const zlib = require("node:zlib");
const assert = require("node:assert/strict");
const NativeMap = globalThis.Map;
const target = path.resolve(process.argv[1]);
const states = new WeakMap();
const records = [];

class AuditMap extends NativeMap {
  constructor(...args) {
    super(...args);
    const caller = new Error().stack.split("\n")[2];
    if (!caller.includes("at counts (") || !caller.includes(target + ":")) return;
    assert.equal(args.length, 0, "Application Map must start with default empty construction");
    const record = { constructor_arguments: args.length, caller, sets: 0, gets: 0,
      cell_updates: 0, events: [] };
    states.set(this, record);
    records.push([this, record]);
  }

  get(key) {
    const record = states.get(this);
    if (record) record.gets++;
    return super.get(key);
  }

  set(key, value) {
    const record = states.get(this);
    if (!record) return super.set(key, value);
    record.sets++;
    assert(Number.isSafeInteger(key) && key >= 0);
    const previous = super.get(key);
    const oldCount = previous === undefined ? 0 :
      typeof previous === "number" ? previous : previous.value;
    if (typeof value === "number") {
      assert.equal(value, oldCount + 1);
      record.events.push([key, oldCount, value]);
    } else {
      assert.equal(previous, undefined, "Cells must only be inserted for new keys");
      assert.deepEqual(Object.keys(value), ["value"]);
      assert.equal(value.value, 1);
      record.events.push([key, 0, 1]);
      value = new Proxy(value, {
        set(cell, property, next) {
          assert.equal(property, "value");
          assert.equal(next, cell.value + 1);
          record.cell_updates++;
          record.events.push([key, cell.value, next]);
          return Reflect.set(cell, property, next);
        }
      });
    }
    return super.set(key, value);
  }
}

globalThis.Map = AuditMap;
process.once("beforeExit", () => {
  const maps = records.map(([table, record]) => ({ ...record,
    entries: Array.from(NativeMap.prototype.entries.call(table), ([key, value]) =>
      [key, typeof value === "number" ? value : value.value]).sort((a, b) => a[0] - b[0])
  }));
  assert.equal(maps.length, 7, "All seven complete histograms must be constructed");
  fs.writeFileSync(process.env.MECH_MAP_WITNESS, zlib.gzipSync(JSON.stringify({
    schema: "typescript-complete-map-runtime-witness.v1", target,
    quantitative_benchmark: false, maps
  })), { flag: "wx" });
});
