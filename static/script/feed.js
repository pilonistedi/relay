// Dark/Light Mode Theme Toggle Logic
function initTheme() {
  const html = document.documentElement;
  const icon = document.getElementById("themeToggleIcon");
  
  // Check localStorage or system preference
  const savedTheme = localStorage.getItem("theme");
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;

  if (savedTheme === "dark" || (!savedTheme && prefersDark)) {
    html.classList.add("dark");
    if (icon) icon.className = "fa-solid fa-sun";
  } else {
    html.classList.remove("dark");
    if (icon) icon.className = "fa-solid fa-moon";
  }
}

function toggleTheme() {
  const html = document.documentElement;
  const icon = document.getElementById("themeToggleIcon");
  
  if (html.classList.contains("dark")) {
    html.classList.remove("dark");
    localStorage.setItem("theme", "light");
    if (icon) icon.className = "fa-solid fa-moon";
  } else {
    html.classList.add("dark");
    localStorage.setItem("theme", "dark");
    if (icon) icon.className = "fa-solid fa-sun";
  }
}

function toggleNexus(target) {
  const tSearch = document.getElementById("tabSearch");
  const tCreate = document.getElementById("tabCreate");
  const aSearch = document.getElementById("nexusSearchArea");
  const aCreate = document.getElementById("nexusCreateArea");

  if (target === "search") {
    aSearch.classList.remove("hidden");
    aCreate.classList.add("hidden");
    tSearch.className =
      "text-neutral-900 dark:text-neutral-100 border-b-2 border-sky-500 pb-1 flex items-center gap-1.5 transition";
    tCreate.className =
      "text-neutral-400 dark:text-neutral-500 hover:text-neutral-600 dark:hover:text-neutral-300 pb-1 flex items-center gap-1.5 transition";
  } else {
    aSearch.classList.add("hidden");
    aCreate.classList.remove("hidden");
    tCreate.className =
      "text-neutral-900 dark:text-neutral-100 border-b-2 border-sky-500 pb-1 flex items-center gap-1.5 transition";
    tSearch.className =
      "text-neutral-400 dark:text-neutral-500 hover:text-neutral-600 dark:hover:text-neutral-300 pb-1 flex items-center gap-1.5 transition";
  }
}

function handleImagePreview(input) {
  const lbl = document.getElementById("lblImg");
  if (input.files && input.files[0]) {
    lbl.innerText = "Loaded: " + input.files[0].name.substring(0, 12) + "...";
    const r = new FileReader();
    r.onload = function (e) {
      const b = document.getElementById("canvasBody");
      b.style.backgroundImage = `url('${e.target.result}')`;
      b.style.backgroundSize = "cover";
    };
    r.readAsDataURL(input.files[0]);
  }
}

// Preset handler storing configuration choice
function applyPreset(tw) {
  const b = document.getElementById("canvasBody");
  b.style.backgroundImage = "";
  b.className =
    "min-h-screen md:h-screen flex flex-col p-4 max-w-5xl mx-auto w-full gap-4 md:overflow-hidden font-sans relative transition-all duration-300 pb-16 md:pb-4 " +
    tw;
  
  const paletteInput = document.getElementById("selectedPaletteInput");
  if (paletteInput) {
    paletteInput.value = tw;
  }
}

function togglePasswordField() {
  const securitySelect = document.getElementById("securityEngineSelect");
  const passwordContainer = document.getElementById("passwordContainer");
  const passwordInput = document.getElementById("groupPasswordInput");

  if (!securitySelect || !passwordContainer || !passwordInput) return;

  if (securitySelect.value === "secure") {
    passwordContainer.classList.remove("hidden");
    passwordInput.required = true;
  } else {
    passwordContainer.classList.add("hidden");
    passwordInput.required = false;
    passwordInput.value = "";
  }
}

// Intercept Form Submissions & DOM initialization
document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  togglePasswordField();

  const form = document.getElementById("nexusCreateArea");
  if (form) {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();

      const submitBtn = form.querySelector("button[type='submit']");
      const originalText = submitBtn ? submitBtn.innerHTML : "Launch Live Group";

      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = "<i class='fa-solid fa-spinner fa-spin mr-1'></i> Launching...";
      }

      try {
        const response = await fetch(form.action, {
          method: "POST",
          body: new FormData(form)
        });

        const data = await response.json();

        if (data.success) {
          window.location.href = "/group/" + data.group_id; 
        } else if (data.redirect_to) {
          window.location.href = data.redirect_to;
        } else {
          alert(data.message || "Failed to launch the live group."); 
          if (submitBtn) {
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
          }
        }
      } catch (error) {
        console.error("Transmission interface crash:", error);
        alert("A system network error occurred while launching the group.");
        if (submitBtn) {
          submitBtn.innerHTML = originalText;
          submitBtn.disabled = false;
        }
      }
    });
  }
});