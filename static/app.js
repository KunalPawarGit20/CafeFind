const cafeGrid = document.querySelector("#cafe-grid");
const emptyState = document.querySelector("#empty-state");
const emptyTitle = document.querySelector("#empty-title");
const emptyCopy = document.querySelector("#empty-copy");
const resultCount = document.querySelector("#result-count");
const notice = document.querySelector("#notice");
const searchForm = document.querySelector("#search-form");
const searchInput = document.querySelector("#location-search");
const addDialog = document.querySelector("#add-dialog");
const addForm = document.querySelector("#add-form");
const formError = document.querySelector("#form-error");

let cafes = [];
let activeFilter = "all";

function showNotice(message, isError = false) {
    notice.textContent = message;
    notice.classList.toggle("notice-error", isError);
    notice.hidden = false;
}

function clearNotice() {
    notice.hidden = true;
    notice.textContent = "";
    notice.classList.remove("notice-error");
}

function safeHttpUrl(value) {
    if (!value) {
        return null;
    }

    try {
        const url = new URL(value);
        return url.protocol === "http:" || url.protocol === "https:" ? url.href : null;
    } catch {
        return null;
    }
}

function addTextElement(parent, tagName, className, text) {
    const element = document.createElement(tagName);
    element.className = className;
    element.textContent = text;
    parent.append(element);
    return element;
}

function addAmenity(parent, icon, label) {
    const item = document.createElement("span");
    const marker = document.createElement("span");
    marker.className = "meta-icon";
    marker.setAttribute("aria-hidden", "true");
    marker.textContent = icon;
    item.append(marker, document.createTextNode(label));
    parent.append(item);
}

function createCafeCard(cafe, index) {
    const card = document.createElement("article");
    card.className = "cafe-card";
    card.style.animationDelay = `${Math.min(index, 5) * 55}ms`;

    const cover = document.createElement("div");
    cover.className = "cafe-cover";
    cover.dataset.theme = String(index % 5);
    const imageUrl = safeHttpUrl(cafe.img_url);
    if (imageUrl) {
        const image = document.createElement("img");
        image.src = imageUrl;
        image.alt = "";
        image.loading = "lazy";
        image.referrerPolicy = "no-referrer";
        image.addEventListener(
            "error",
            () => {
                image.remove();
                cover.classList.add("cover-placeholder");
            },
            { once: true }
        );
        cover.append(image);
    } else {
        cover.classList.add("cover-placeholder");
    }
    addTextElement(cover, "span", "cover-label", cafe.can_take_calls ? "Work & unwind" : "Your next coffee");
    card.append(cover);

    const body = document.createElement("div");
    body.className = "cafe-card-body";
    addTextElement(body, "p", "cafe-location", cafe.location || "Local favorite");
    addTextElement(body, "h3", "cafe-name", cafe.name || "Untitled cafe");

    const meta = document.createElement("div");
    meta.className = "cafe-meta";
    if (cafe.seats) {
        addAmenity(meta, "◌", `${cafe.seats} seats`);
    }
    if (cafe.has_wifi) {
        addAmenity(meta, "⌁", "Wi-Fi");
    }
    if (cafe.has_sockets) {
        addAmenity(meta, "ϟ", "Outlets");
    }
    if (cafe.has_toilet) {
        addAmenity(meta, "＋", "Restroom");
    }
    if (cafe.can_take_calls) {
        addAmenity(meta, "◖", "Calls okay");
    }
    body.append(meta);

    const footer = document.createElement("div");
    footer.className = "cafe-card-footer";
    addTextElement(
        footer,
        "span",
        "coffee-price",
        cafe.coffee_price ? `Coffee ${cafe.coffee_price}` : "A good cup awaits"
    );
    const mapUrl = safeHttpUrl(cafe.map_url);
    if (mapUrl) {
        const mapLink = document.createElement("a");
        mapLink.className = "map-link";
        mapLink.href = mapUrl;
        mapLink.target = "_blank";
        mapLink.rel = "noopener noreferrer";
        mapLink.textContent = "Get directions ";
        const arrow = document.createElement("span");
        arrow.setAttribute("aria-hidden", "true");
        arrow.textContent = "↗";
        mapLink.append(arrow);
        footer.append(mapLink);
    }
    body.append(footer);
    card.append(body);
    return card;
}

function filteredCafes() {
    if (activeFilter === "all") {
        return cafes;
    }

    const propertyByFilter = {
        wifi: "has_wifi",
        sockets: "has_sockets",
        calls: "can_take_calls",
    };
    const property = propertyByFilter[activeFilter];
    return cafes.filter((cafe) => cafe[property]);
}

function renderCafes() {
    const visibleCafes = filteredCafes();
    cafeGrid.replaceChildren(...visibleCafes.map(createCafeCard));
    resultCount.textContent = `${visibleCafes.length} ${visibleCafes.length === 1 ? "spot" : "spots"}`;
    emptyState.hidden = visibleCafes.length > 0;

    if (cafes.length > 0 && visibleCafes.length === 0) {
        emptyTitle.textContent = "No spots match that filter.";
        emptyCopy.textContent = "Try another amenity or browse all cafes.";
        document.querySelector("#empty-add-button").hidden = true;
    } else {
        emptyTitle.textContent = "Your next favorite is out there.";
        emptyCopy.textContent = cafes.length
            ? "No cafes match that location yet. Try another place or add a favorite."
            : "No cafes here just yet. Add the first spot and help the neighborhood out.";
        document.querySelector("#empty-add-button").hidden = false;
    }
}

async function loadCafes(endpoint = "/all") {
    clearNotice();
    resultCount.textContent = "Finding spots...";
    try {
        const response = await fetch(endpoint, {
            headers: { Accept: "application/json" },
        });
        const payload = await response.json();
        if (!response.ok) {
            if (response.status === 404 && endpoint.startsWith("/search")) {
                cafes = [];
                renderCafes();
                emptyTitle.textContent = "No cafes found there.";
                emptyCopy.textContent =
                    "Try a nearby neighborhood or add a cafe you love.";
                return;
            }
            throw new Error(payload.error?.message || "We couldn't find those cafes.");
        }

        cafes = Array.isArray(payload.cafes)
            ? payload.cafes
            : payload.cafe
              ? [payload.cafe]
              : [];
        renderCafes();
    } catch (error) {
        cafes = [];
        renderCafes();
        showNotice(error.message || "Something went wrong while loading cafes.", true);
    }
}

function setActiveFilter(filter) {
    activeFilter = filter;
    document.querySelectorAll(".filter-chip").forEach((button) => {
        const isActive = button.dataset.filter === filter;
        button.classList.toggle("is-active", isActive);
        button.setAttribute("aria-pressed", String(isActive));
    });
    renderCafes();
}

function openAddDialog() {
    formError.hidden = true;
    addDialog.showModal();
}

document.querySelector("#open-add-dialog").addEventListener("click", openAddDialog);
document.querySelector("#empty-add-button").addEventListener("click", openAddDialog);
document.querySelector("#about-add-button").addEventListener("click", openAddDialog);
document.querySelector("#close-add-dialog").addEventListener("click", () => addDialog.close());

addDialog.addEventListener("click", (event) => {
    if (event.target === addDialog) {
        addDialog.close();
    }
});

searchForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const location = searchInput.value.trim();
    setActiveFilter("all");
    loadCafes(location ? `/search?loc=${encodeURIComponent(location)}` : "/all");
});

document.querySelector("#random-cafe").addEventListener("click", () => {
    setActiveFilter("all");
    loadCafes("/random");
});

document.querySelector("#show-all").addEventListener("click", () => {
    searchInput.value = "";
    setActiveFilter("all");
    loadCafes("/all");
});

document.querySelectorAll(".filter-chip").forEach((button) => {
    button.addEventListener("click", () => setActiveFilter(button.dataset.filter));
});

addForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    formError.hidden = true;
    const submitButton = addForm.querySelector('button[type="submit"]');
    submitButton.disabled = true;
    submitButton.textContent = "Adding your spot...";

    try {
        const response = await fetch("/add", {
            method: "POST",
            headers: {
                Accept: "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            body: new URLSearchParams(new FormData(addForm)),
        });
        const payload = await response.json();
        if (!response.ok) {
            throw new Error(payload.error?.message || "We couldn't add that cafe.");
        }

        addForm.reset();
        addDialog.close();
        searchInput.value = "";
        setActiveFilter("all");
        await loadCafes("/all");
        showNotice("Cafe added. Thanks for sharing a good spot!");
    } catch (error) {
        formError.textContent = error.message || "Something went wrong. Please try again.";
        formError.hidden = false;
    } finally {
        submitButton.disabled = false;
        submitButton.innerHTML = 'Add to the list <span aria-hidden="true">→</span>';
    }
});

loadCafes();
