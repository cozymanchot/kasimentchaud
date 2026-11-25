// Shared behavior only. All page content and markup live in the HTML files.
const editing = new URLSearchParams(window.location.search).has("edit");

for (const year of document.querySelectorAll("[data-year]")) {
  year.textContent = String(new Date().getFullYear());
}

const menuButton = document.querySelector("[data-menu-toggle]");
const mobileNavigation = document.querySelector("#mobile-navigation");
menuButton?.addEventListener("click", () => {
  mobileNavigation.hidden = !mobileNavigation.hidden;
  menuButton.setAttribute("aria-expanded", String(!mobileNavigation.hidden));
});

const newsletterForm = document.querySelector("[data-newsletter-form]");
newsletterForm?.addEventListener("submit", (event) => {
  event.preventDefault();
  newsletterForm.hidden = true;
  document.querySelector("[data-newsletter-success]").hidden = false;
});

const contactForm = document.querySelector("[data-contact-form]");
const enquiry = new URLSearchParams(window.location.search);
const message = contactForm?.querySelector('[name="message"]');
if (message && enquiry.get("produit") && !message.value) {
  const size = enquiry.get("taille");
  message.value = `Bonjour! Je souhaite commander ${enquiry.get("produit")}${size ? `, taille ${size}` : ""}. Est-ce disponible?`;
}
contactForm?.addEventListener("submit", (event) => {
  event.preventDefault();
  contactForm.hidden = true;
  document.querySelector("[data-contact-preview]").textContent = message.value;
  document.querySelector("[data-contact-success]").hidden = false;
});

const shop = document.querySelector("[data-shop]");
if (shop) {
  const cards = Array.from(shop.querySelectorAll("[data-product-card]"));
  const grid = shop.querySelector("[data-products]");
  const sort = shop.querySelector("[data-sort]");
  let category = shop.dataset.category;
  let size = "all";
  let color = "all";

  function updateShop() {
    const categoryCards = cards.filter(
      (card) => category === "all" || card.dataset.category === category,
    );
    const sizes = new Set(categoryCards.flatMap((card) => card.dataset.sizes.split("|")));
    const colors = new Set(categoryCards.map((card) => card.dataset.color));
    for (const button of shop.querySelectorAll("[data-filter] button")) {
      const filter = button.parentElement.dataset.filter;
      const value = button.dataset.value;
      const selected = { category, size, color }[filter];
      button.setAttribute("aria-pressed", String(value === selected));
      button.hidden =
        value !== "all" &&
        ((filter === "size" && !sizes.has(value)) || (filter === "color" && !colors.has(value)));
    }

    let visibleCount = 0;
    for (const card of cards) {
      const matches =
        categoryCards.includes(card) &&
        (size === "all" || card.dataset.sizes.split("|").includes(size)) &&
        (color === "all" || card.dataset.color === color);
      card.hidden = !matches;
      if (matches) visibleCount++;
    }
    const ordered = [...cards];
    if (sort?.value === "asc") {
      ordered.sort((first, second) => Number(first.dataset.price) - Number(second.dataset.price));
    }
    if (sort?.value === "desc") {
      ordered.sort((first, second) => Number(second.dataset.price) - Number(first.dataset.price));
    }
    grid.append(...ordered);
    shop.querySelector("[data-shop-empty]").hidden = visibleCount > 0;
  }

  shop.addEventListener("click", (event) => {
    const button = event.target.closest("[data-filter] button");
    if (!button) return;
    const filter = button.parentElement.dataset.filter;
    if (filter === "category") {
      category = button.dataset.value;
      size = "all";
      color = "all";
    }
    if (filter === "size") size = button.dataset.value;
    if (filter === "color") color = button.dataset.value;
    updateShop();
  });
  sort?.addEventListener("change", updateShop);
  updateShop();
}

const productPage = document.querySelector("[data-product]");
if (productPage) {
  const orderLink = productPage.querySelector("[data-order-link]");
  const sizeButtons = Array.from(productPage.querySelectorAll("[data-size]"));
  let selectedSize = sizeButtons[0]?.dataset.size || "";

  function updateProduct() {
    for (const button of sizeButtons) {
      button.setAttribute("aria-pressed", String(button.dataset.size === selectedSize));
    }
    if (orderLink) {
      const query = new URLSearchParams({
        produit: productPage.querySelector("[data-product-name]").textContent.trim(),
      });
      if (selectedSize) query.set("taille", selectedSize);
      orderLink.href = `/contact/?${query}#message`;
    }
  }

  for (const button of sizeButtons) {
    button.addEventListener("click", () => {
      selectedSize = button.dataset.size;
      updateProduct();
    });
  }
  for (const thumbnail of productPage.querySelectorAll("[data-product-view]")) {
    thumbnail.addEventListener("click", () => {
      const visual = productPage.querySelector("[data-main-visual]");
      const artwork = thumbnail.querySelector("svg").cloneNode(true);
      const pattern = artwork.querySelector("pattern");
      const previousId = pattern.id;
      pattern.id = previousId + "-main";
      for (const shape of artwork.querySelectorAll(`[fill="url(#${previousId})"]`)) {
        shape.setAttribute("fill", `url(#${pattern.id})`);
      }
      visual.replaceChildren(...artwork.childNodes);
      for (const button of productPage.querySelectorAll("[data-product-view]")) {
        button.setAttribute("aria-pressed", String(button === thumbnail));
      }
    });
  }
  updateProduct();
}

// Authoring view shows normally conditional content for visual selection.
if (editing) {
  for (const details of document.querySelectorAll("details")) details.open = true;
  for (const state of document.querySelectorAll(
    "[data-newsletter-success], [data-contact-success], [data-shop-empty]",
  )) {
    state.hidden = false;
  }
}
