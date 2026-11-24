import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";
import test from "node:test";

const source = readFileSync(new URL("../site.js", import.meta.url), "utf8");

function initialize(elements, search = "") {
  vm.runInNewContext(source, {
    URLSearchParams,
    window: { location: { search } },
    document: {
      querySelector: (selector) => elements[selector] ?? null,
      querySelectorAll: () => [],
    },
  });
}

test("product enquiries carry the selected size and product name to contact", () => {
  const orderLink = {};
  const sizes = ["M", "L"].map((size) => ({
    dataset: { size },
    setAttribute(_name, value) {
      this.pressed = value;
    },
    addEventListener(_event, handler) {
      this.click = handler;
    },
  }));
  initialize({
    "[data-product]": {
      querySelector: (selector) =>
        selector === "[data-order-link]"
          ? orderLink
          : { textContent: "Le Câlin Caramel" },
      querySelectorAll: (selector) => (selector === "[data-size]" ? sizes : []),
    },
  });
  let destination = new URL(orderLink.href, "https://example.test");
  assert.equal(destination.pathname, "/contact/");
  assert.equal(destination.hash, "#message");
  assert.equal(destination.searchParams.get("produit"), "Le Câlin Caramel");
  assert.equal(destination.searchParams.get("taille"), "M");
  sizes[1].click();
  destination = new URL(orderLink.href, "https://example.test");
  assert.equal(destination.searchParams.get("taille"), "L");
  assert.equal(sizes[0].pressed, "false");
  assert.equal(sizes[1].pressed, "true");
});

test("contact prefill keeps product details as text and preserves a written message", () => {
  const message = { value: "" };
  const preview = {};
  const success = { hidden: true };
  let submit;
  const contact = {
    querySelector: () => message,
    addEventListener(_event, handler) {
      submit = handler;
    },
  };
  const elements = {
    "[data-contact-form]": contact,
    "[data-contact-preview]": preview,
    "[data-contact-success]": success,
  };
  const search = "?" + new URLSearchParams({ produit: "Le Câlin Caramel", taille: "L" });
  initialize(elements, search);
  assert.equal(
    message.value,
    "Bonjour! Je souhaite commander Le Câlin Caramel, taille L. Est-ce disponible?",
  );
  message.value = "Ma question personnelle";
  initialize(elements, search);
  assert.equal(message.value, "Ma question personnelle");
  let prevented = false;
  submit({ preventDefault() { prevented = true; } });
  assert.equal(prevented, true);
  assert.equal(preview.textContent, "Ma question personnelle");
  assert.equal(contact.hidden, true);
  assert.equal(success.hidden, false);
});
