const feed = document.getElementById("feed");
const statusEl = document.getElementById("status");
const MAX_CARDS = 6;

const WS_URL = `ws://${window.location.hostname}:8765/ws`;
let ws;

function connect() {
  ws = new WebSocket(WS_URL);

  ws.onopen = () => { statusEl.textContent = "connected"; statusEl.style.color = "#5dcaa5"; };
  ws.onclose = () => {
    statusEl.textContent = "reconnecting...";
    statusEl.style.color = "#ef9f27";
    setTimeout(connect, 2000);
  };

  ws.onmessage = (e) => {
    try { renderCard(JSON.parse(e.data)); }
    catch { console.warn("Bad signal JSON", e.data); }
  };
}

function renderCard(signal) {
  const type = signal.type || "benchmark";
  const card = document.createElement("div");
  card.className = "card";
  card.innerHTML = `
    <div class="card-top">
      <span class="badge badge-${type}">${type}</span>
      <span class="card-title">${signal.title || ""}</span>
    </div>
    <div class="card-body">${signal.body || ""}</div>
    ${signal.suggested_response
      ? `<div class="card-response">"${signal.suggested_response}"</div>`
      : ""}
    <div class="card-evidence">${signal.evidence || ""}</div>
    <div class="card-footer">
      <button class="copy-btn" onclick="copyCard(this)">copy</button>
    </div>
  `;
  feed.prepend(card);
  while (feed.children.length > MAX_CARDS) feed.removeChild(feed.lastChild);
}

function copyCard(btn) {
  const card = btn.closest(".card");
  const title = card.querySelector(".card-title").textContent;
  const body  = card.querySelector(".card-body").textContent;
  const resp  = card.querySelector(".card-response");
  const text  = resp ? `${title}\n${body}\nSay: ${resp.textContent}` : `${title}\n${body}`;
  navigator.clipboard.writeText(text);
  btn.textContent = "copied";
  setTimeout(() => btn.textContent = "copy", 1500);
}

connect();
