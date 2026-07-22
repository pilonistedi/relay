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

document.addEventListener("DOMContentLoaded", () => {
  // ... existing init code ...

  const searchInput = document.getElementById("groupSearchInput");
  const dropdown = document.getElementById("autocompleteDropdown");
  const resultsContainer = document.getElementById("searchResultsContainer");

  let debounceTimer = null;

  if (searchInput && dropdown) {
    searchInput.addEventListener("input", (e) => {
      const query = e.target.value.trim();

      clearTimeout(debounceTimer);

      if (!query) {
        dropdown.classList.add("hidden");
        dropdown.innerHTML = "";
        return;
      }

      // Debounce to prevent unnecessary fetch requests while typing
      debounceTimer = setTimeout(async () => {
        try {
          const res = await fetch(`/api/search_groups?q=${encodeURIComponent(query)}`);
          const groups = await res.json();

          if (groups.length === 0) {
            dropdown.innerHTML = `
              <div class="p-2 text-[11px] text-neutral-400 dark:text-neutral-500 text-center">
                No matching groups found
              </div>`;
          } else {
            dropdown.innerHTML = groups.map(g => `
              <a 
                href="/group/${g.id}" 
                class="flex items-center gap-2 p-2 hover:bg-neutral-100 dark:hover:bg-neutral-800 text-xs transition border-b border-neutral-100 dark:border-neutral-800/50 last:border-0"
              >
                <span class="text-sm">${g.icon}</span>
                <span class="font-medium text-neutral-800 dark:text-neutral-200">${g.group_name}</span>
              </a>
            `).join('');

            // Optionally update the cards view underneath dynamically
            updateSearchResultsCards(groups);
          }

          dropdown.classList.remove("hidden");
        } catch (err) {
          console.error("Search fetch error:", err);
        }
      }, 250);
    });

    // Close autocomplete when clicking outside
    document.addEventListener("click", (e) => {
      if (!searchInput.contains(e.target) && !dropdown.contains(e.target)) {
        dropdown.classList.add("hidden");
      }
    });
  }

  function updateSearchResultsCards(groups) {
    if (!resultsContainer) return;

    if (groups.length === 0) {
      resultsContainer.innerHTML = `
        <div class="text-center py-6 text-xs text-neutral-400">
          No groups match your search query.
        </div>`;
      return;
    }

    resultsContainer.innerHTML = groups.map(g => `
      <a
        class="block p-2.5 rounded-lg bg-neutral-50/50 dark:bg-neutral-800/40 border border-neutral-200/80 dark:border-neutral-800 hover:border-sky-500/50 dark:hover:border-sky-500/40 hover:bg-white dark:hover:bg-neutral-800/70 transition-all text-xs group"
        href="/group/${g.id}"
      >
        <div class="flex justify-between items-center">
          <span class="font-bold text-neutral-900 dark:text-neutral-100 text-[11px] truncate group-hover:text-sky-600 dark:group-hover:text-sky-400 transition-colors">
            ${g.icon} ${g.group_name}
          </span>
          <span class="text-[9px] text-sky-700 dark:text-sky-400 font-mono bg-sky-50 dark:bg-sky-950/60 px-1.5 py-0.5 rounded border border-sky-200/60 dark:border-sky-800/60 shrink-0 ml-2">
            Active
          </span>
        </div>
      </a>
    `).join('');
  }
});