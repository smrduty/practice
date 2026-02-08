let showOnlyFavorites = false;

async function load(q = "") {
  const params = new URLSearchParams();
  params.set("limit", 1000);
  if (q) params.set("q", q);

  const res = await fetch("/api/vacancies?" + params.toString());
  const data = await res.json();
  const tbody = document.querySelector("#vacancies tbody");
  tbody.innerHTML = "";

  data.items
  .filter(item => !showOnlyFavorites || Number(item.is_favorite) === 1)
  .forEach(item => {
    const tr = document.createElement("tr");
    const isFav = Number(item.is_favorite);
    tr.innerHTML = `
      <td>${item.id}</td>
      <td>${item.title || ""}</td>
      <td>${item.salary || ""}</td>
      <td>${item.experience || ""}</td>
      <td>${item.address || ""}</td>
      <td>${item.url ? `<a href="${item.url}" target="_blank">link</a>` : ""}</td>
      <td>${item.parsed_at || ""}</td>
      <td>
        <button onclick="sendToTelegram(${item.id})">📨</button>
        <button onclick="deleteVacancy(${item.id})">❌</button>
        <button onclick="toggleFavorite(${item.id}, ${isFav})">
          ${favoriteIcon(isFav)}
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });

  loadVacanciesCount()
}

function favoriteIcon(isFavorite) {
  return isFavorite ? "⭐" : "🤍";
}

async function toggleFavorite(id, isFavorite) {
  const url = isFavorite ? `/api/vacancies/${id}/unfavorite` : `/api/vacancies/${id}/favorite`;

  await fetch(url, {method: "POST"});
  
  load();
}

async function loadVacanciesCount() {
  const response = await fetch(`/api/stats/count?`);
  const data = await response.json();

  console.log("count called", data.total, document.getElementById("total-vacancies"));

  document.getElementById("total-vacancies").textContent = data.total;
  return;

}

async function deleteVacancy(id) {
  if(!confirm("Удалить вакансию?")) return;

  const res = await fetch(`/api/vacancies/${id}`, {
    method: "DELETE"
  });

  if (!res.ok) {
    alert("Ошибка при удалении");
    return;
  }

  const q = document.getElementById("q").value.trim();
  load(q);
}

async function sendToTelegram(id) {
  const res = await fetch(`/api/vacancies/${id}/send_to_tg`, {
    method: "POST"
  });

  if (!res.ok) {
    alert("Ошибка отправки в Telegram");
    return;
  }

  alert("Отправлено в Telegram ✅");
}

document.getElementById("refresh").addEventListener("click", () => {
  const q = document.getElementById("q").value.trim();
  load(q);
});

// document.getElementById("header-favorites-btn").addEventListener("click", () => {
//   alert("pyk");
//   showOnlyFavorites = !showOnlyFavorites;

//   const btn = document.getElementById("header-favorites-btn");
//   btn.textContent = showOnlyFavorites ? "📋 Vse вакансии" : "⭐ Избранные";

//   btn.classList.toggle("active", showOnlyFavorites);

//   const q = document.getElementById("q").value.trim();
//   load(q);
// });

// initial load
document.addEventListener("DOMContentLoaded", () => {
  load();
  const favBtn = document.getElementById("header-favorites-btn");
  if (!favBtn) {
    console.error("header-favorites-btn not found");
    return;
  }

  favBtn.addEventListener("click", () => {
    showOnlyFavorites = !showOnlyFavorites;

    favBtn.textContent = showOnlyFavorites
      ? "📋 Все вакансии"
      : "⭐ Избранные";

    favBtn.classList.toggle("active", showOnlyFavorites);

    const q = document.getElementById("q").value.trim();
    load(q);
  });
});