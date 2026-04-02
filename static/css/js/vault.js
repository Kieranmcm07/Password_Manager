// ── Clipboard helpers ─────────────────────────────────────

// Copy from a visible text element (span, div)
function copyText(elementId, btn) {
    const el = document.getElementById(elementId);
    if (!el) return;
    navigator.clipboard.writeText(el.textContent.trim()).then(() => {
        flashButton(btn, "Copied!");
    }).catch(() => {
        alert("Copy failed. Your browser may not support clipboard access.");
    });
}

// Copy from an input or password field
function copyFromInput(inputId, btn) {
    const el = document.getElementById(inputId);
    if (!el) return;
    navigator.clipboard.writeText(el.value).then(() => {
        flashButton(btn, "Copied!");
    }).catch(() => {
        alert("Copy failed.");
    });
}

// Briefly change the button text to give feedback, then reset it
function flashButton(btn, message) {
    if (!btn) return;
    const original = btn.textContent;
    btn.textContent = message;
    setTimeout(() => {
        btn.textContent = original;
    }, 1500);
}


// ── Show / hide password fields ───────────────────────────

function togglePwField(inputId, btn) {
    const input = document.getElementById(inputId);
    if (!input) return;
    if (input.type === "password") {
        input.type = "text";
        btn.textContent = "Hide";
    } else {
        input.type = "password";
        btn.textContent = "Show";
    }
}


// ── Password generator ────────────────────────────────────

const CHARS = {
    upper: "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    lower: "abcdefghijklmnopqrstuvwxyz",
    numbers: "0123456789",
    symbols: "!@#$%^&*()_+-=[]{}|;:,.<>?",
};

function generatePassword(length, useUpper, useLower, useNumbers, useSymbols) {
    let charset = "";
    if (useUpper)   charset += CHARS.upper;
    if (useLower)   charset += CHARS.lower;
    if (useNumbers) charset += CHARS.numbers;
    if (useSymbols) charset += CHARS.symbols;

    if (charset === "") return "";

    // Use the Web Crypto API for proper randomness
    const randomBytes = new Uint32Array(length);
    window.crypto.getRandomValues(randomBytes);

    let result = "";
    for (let i = 0; i < length; i++) {
        result += charset[randomBytes[i] % charset.length];
    }
    return result;
}

// Called by the Generator page button
function runGenerator() {
    const length   = parseInt(document.getElementById("pw-length").value, 10);
    const useUpper   = document.getElementById("opt-upper").checked;
    const useLower   = document.getElementById("opt-lower").checked;
    const useNumbers = document.getElementById("opt-numbers").checked;
    const useSymbols = document.getElementById("opt-symbols").checked;

    const pw = generatePassword(length, useUpper, useLower, useNumbers, useSymbols);
    if (!pw) {
        alert("Select at least one character type.");
        return;
    }
    document.getElementById("generated-pw").value = pw;
}

// Called from the add/edit entry form — fills the password field with a generated password
function fillGenerated(inputId) {
    const pw = generatePassword(20, true, true, true, false);
    const input = document.getElementById(inputId);
    if (input && pw) {
        input.value = pw;
        input.type = "text"; // Show it so the user can see what was generated
    }
}