function flashButton(btn, message) {
  if (!btn) return;
  const original = btn.textContent;
  btn.textContent = message;
  setTimeout(() => {
    btn.textContent = original;
  }, 1500);
}

function copyText(elementId, btn) {
  const el = document.getElementById(elementId);
  if (!el) {
    console.error("copyText: element not found:", elementId);
    return;
  }

  const text = (el.textContent || "").trim();

  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard
      .writeText(text)
      .then(() => flashButton(btn, "Copied!"))
      .catch((err) => {
        console.error("Clipboard write failed:", err);
        fallbackCopy(text, btn);
      });
  } else {
    fallbackCopy(text, btn);
  }
}

function copyFromInput(inputId, btn) {
  const el = document.getElementById(inputId);
  if (!el) {
    console.error("copyFromInput: input not found:", inputId);
    return;
  }

  const text = el.value || "";

  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard
      .writeText(text)
      .then(() => flashButton(btn, "Copied!"))
      .catch((err) => {
        console.error("Clipboard write failed:", err);
        fallbackCopy(text, btn);
      });
  } else {
    fallbackCopy(text, btn);
  }
}

function fallbackCopy(text, btn) {
  const temp = document.createElement("textarea");
  temp.value = text;
  temp.setAttribute("readonly", "");
  temp.style.position = "absolute";
  temp.style.left = "-9999px";
  document.body.appendChild(temp);
  temp.select();

  try {
    document.execCommand("copy");
    flashButton(btn, "Copied!");
  } catch (err) {
    console.error("Fallback copy failed:", err);
    alert("Copy failed.");
  }

  document.body.removeChild(temp);
}

function togglePwField(inputId, btn) {
  const input = document.getElementById(inputId);
  if (!input) {
    console.error("togglePwField: input not found:", inputId);
    return;
  }

  if (input.type === "password") {
    input.type = "text";
    if (btn) btn.textContent = "Hide";
  } else {
    input.type = "password";
    if (btn) btn.textContent = "Show";
  }
}

const CHARS = {
  upper: "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
  lower: "abcdefghijklmnopqrstuvwxyz",
  numbers: "0123456789",
  symbols: "!@#$%^&*()_+-=[]{}|;:,.<>?",
};

function generatePassword(length, useUpper, useLower, useNumbers, useSymbols) {
  let charset = "";
  if (useUpper) charset += CHARS.upper;
  if (useLower) charset += CHARS.lower;
  if (useNumbers) charset += CHARS.numbers;
  if (useSymbols) charset += CHARS.symbols;

  if (!charset) return "";

  const randomBytes = new Uint32Array(length);
  crypto.getRandomValues(randomBytes);

  let result = "";
  for (let i = 0; i < length; i++) {
    result += charset[randomBytes[i] % charset.length];
  }
  return result;
}

function runGenerator() {
  const lengthEl = document.getElementById("pw-length");
  const upperEl = document.getElementById("opt-upper");
  const lowerEl = document.getElementById("opt-lower");
  const numbersEl = document.getElementById("opt-numbers");
  const symbolsEl = document.getElementById("opt-symbols");
  const outputEl = document.getElementById("generated-pw");

  if (
    !lengthEl ||
    !upperEl ||
    !lowerEl ||
    !numbersEl ||
    !symbolsEl ||
    !outputEl
  ) {
    console.error("runGenerator: one or more generator elements are missing");
    return;
  }

  const length = parseInt(lengthEl.value, 10);
  const pw = generatePassword(
    length,
    upperEl.checked,
    lowerEl.checked,
    numbersEl.checked,
    symbolsEl.checked,
  );

  if (!pw) {
    alert("Select at least one character type.");
    return;
  }

  outputEl.value = pw;
}

function fillGenerated(inputId) {
  const input = document.getElementById(inputId);
  if (!input) {
    console.error("fillGenerated: input not found:", inputId);
    return;
  }

  const pw = generatePassword(20, true, true, true, false);
  if (!pw) return;

  input.value = pw;
  input.type = "text";
}

function toggleTheme() {
  const body = document.body;
  body.classList.toggle("dark-mode");

  const isDark = body.classList.contains("dark-mode");
  localStorage.setItem("theme", isDark ? "dark" : "light");
}

document.addEventListener("DOMContentLoaded", () => {
  const savedTheme = localStorage.getItem("theme");
  if (savedTheme === "dark") {
    document.body.classList.add("dark-mode");
  }
});
