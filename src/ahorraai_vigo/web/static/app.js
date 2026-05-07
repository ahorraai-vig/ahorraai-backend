const offersGrid = document.getElementById("offers-grid");
const marketplaceStatus = document.getElementById("marketplace-status");
const reloadButton = document.getElementById("reload-offers");

function formatPrice(priceAmount, currency) {
  if (priceAmount === null || priceAmount === undefined) {
    return "Consultar";
  }

  const numericValue = Number(priceAmount);
  if (Number.isNaN(numericValue)) {
    return `${priceAmount} ${currency}`;
  }

  return new Intl.NumberFormat("es-ES", {
    style: "currency",
    currency,
  }).format(numericValue);
}

function renderEmptyState(message) {
  offersGrid.innerHTML = `<div class="offer-card__empty">${message}</div>`;
}

function renderOffers(offers) {
  if (!offers.length) {
    marketplaceStatus.textContent =
      "Todavía no hay ofertas en la base de datos. Cuando un negocio publique una, aparecerá aquí.";
    renderEmptyState("Aún no hay ofertas activas en Vigo.");
    return;
  }

  marketplaceStatus.textContent = `Mostrando ${offers.length} oferta(s) activas conectadas al backend real.`;

  offersGrid.innerHTML = offers
    .map(
      (offer) => `
        <article class="offer-card">
          <div class="offer-card__meta">
            <span>${offer.business_name}</span>
            <span>${offer.city_slug}</span>
          </div>
          <div>
            <h3>${offer.title}</h3>
            <p>${offer.description}</p>
          </div>
          <span class="offer-card__price">${formatPrice(offer.price_amount, offer.currency)}</span>
        </article>
      `,
    )
    .join("");
}

async function loadOffers() {
  marketplaceStatus.textContent = "Cargando ofertas desde la API...";
  reloadButton.disabled = true;

  try {
    const response = await fetch("/api/v1/offers?limit=6");
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const offers = await response.json();
    renderOffers(offers);
  } catch (error) {
    marketplaceStatus.textContent =
      "No pude cargar las ofertas ahora mismo. Revisa si el backend y la base de datos están levantados.";
    renderEmptyState("Error al cargar ofertas. Inténtalo de nuevo en unos segundos.");
    console.error(error);
  } finally {
    reloadButton.disabled = false;
  }
}

reloadButton?.addEventListener("click", loadOffers);
loadOffers();
