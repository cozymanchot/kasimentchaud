import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";
import test from "node:test";

const source = readFileSync(new URL("../site.js", import.meta.url), "utf8");

function loadGallery(prices, sortValue) {
  const cards = prices.map((price) => ({
    dataset: {
      price: String(price),
      category: "couvertures",
      sizes: "Petit format",
      color: "Beige",
    },
  }));
  const emptyState = { hidden: true };
  let rendered = [];
  let sortListener;
  const sort = sortValue
    ? {
        value: sortValue,
        addEventListener(_event, callback) {
          sortListener = callback;
        },
      }
    : null;
  const gallery = {
    dataset: { category: "all" },
    querySelectorAll(selector) {
      return selector === "[data-product-card]" ? cards : [];
    },
    querySelector(selector) {
      return {
        "[data-products]": {
          append(...items) {
            rendered = items;
          },
        },
        "[data-sort]": sort,
        "[data-shop-empty]": emptyState,
      }[selector];
    },
    addEventListener() {},
  };
  vm.runInNewContext(source, {
    URLSearchParams,
    window: { location: { search: "" }, addEventListener() {} },
    localStorage: {
      getItem() {
        return "[]";
      },
    },
    document: {
      querySelector(selector) {
        return selector === "[data-shop]" ? gallery : null;
      },
      querySelectorAll() {
        return [];
      },
    },
  });
  return { rendered, emptyState, sortListener };
}

test("a visual gallery without sorting controls initializes normally", () => {
  const { rendered, emptyState } = loadGallery([35]);
  assert.equal(rendered.length, 1);
  assert.equal(rendered[0].hidden, false);
  assert.equal(emptyState.hidden, true);
});

test("an empty gallery without sorting controls displays its empty state", () => {
  assert.equal(loadGallery([]).emptyState.hidden, false);
});

test("sorting still works on pages that retain the control", () => {
  const { rendered, sortListener } = loadGallery([68, 35], "asc");
  assert.deepEqual(
    rendered.map((card) => Number(card.dataset.price)),
    [35, 68],
  );
  assert.equal(typeof sortListener, "function");
});
