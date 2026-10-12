const chatEl = document.getElementById("chat");
const formEl = document.getElementById("chatForm");
const inputEl = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");
const resetBtn = document.getElementById("resetBtn");
const modelSelect = document.getElementById("modelSelect");

// Same-origin backend. If you serve the frontend separately from the API,
// change this to e.g. "http://localhost:5000/api/chat".
const API_URL = "/api/chat";

let history = [];

function addMessage(role, text) {
  const wrapper = document.createElement("div");
  wrapper.className = `message message--${role}`;
  const avatar = document.createElement("div");
  avatar.className = "message__avatar";
  avatar.textContent = role === "user" ? "🧑" : "🤖";
  const bubble = document.createElement("div");
  bubble.className = "message__bubble";
  bubble.textContent = text;
  wrapper.appendChild(avatar);
  wrapper.appendChild(bubble);
  chatEl.appendChild(wrapper);
  chatEl.scrollTop = chatEl.scrollHeight;
  return bubble;
}

function addTypingIndicator() {
  const wrapper = document.createElement("div");
  wrapper.className = "message message--bot message--typing";
  wrapper.id = "typingIndicator";
  const avatar = document.createElement("div");
  avatar.className = "message__avatar";
  avatar.textContent = "🤖";
  const bubble = document.createElement("div");
  bubble.className = "message__bubble";
  bubble.textContent = "Thinking through the problem...";
  wrapper.appendChild(avatar);
  wrapper.appendChild(bubble);
  chatEl.appendChild(wrapper);
  chatEl.scrollTop = chatEl.scrollHeight;
}

function removeTypingIndicator() {
  const el = document.getElementById("typingIndicator");
  if (el) el.remove();
}

async function callBackend(userMessage) {
  history.push({ role: "user", content: userMessage });
  history = history.slice(-20);

  const res = await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      messages: history,
      model: modelSelect.value,
    }),
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.error || `Server error (${res.status})`);
  }

  history.push({ role: "assistant", content: data.reply });
  return data.reply;
}

formEl.addEventListener("submit", async (e) => {
  e.preventDefault();
  const message = inputEl.value.trim();
  if (!message) return;

  addMessage("user", message);
  inputEl.value = "";
  inputEl.style.height = "auto";
  sendBtn.disabled = true;
  addTypingIndicator();

  try {
    const reply = await callBackend(message);
    removeTypingIndicator();
    addMessage("bot", reply);
  } catch (err) {
    removeTypingIndicator();
    addMessage("bot", `⚠️ ${err.message}`);
  } finally {
    sendBtn.disabled = false;
    inputEl.focus();
  }
});

inputEl.addEventListener("input", () => {
  inputEl.style.height = "auto";
  inputEl.style.height = Math.min(inputEl.scrollHeight, 160) + "px";
});

inputEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    formEl.requestSubmit();
  }
});

resetBtn.addEventListener("click", () => {
  history = [];
  chatEl.innerHTML = "";
  addMessage("bot", "New chat started. Paste a problem or ask about a concept whenever you're ready.");
});
