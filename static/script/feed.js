function toggleNexus(target) {
  const tSearch = document.getElementById("tabSearch");
  const tCreate = document.getElementById("tabCreate");
  const aSearch = document.getElementById("nexusSearchArea");
  const aCreate = document.getElementById("nexusCreateArea");

  if (target === "search") {
    aSearch.classList.remove("hidden");
    aCreate.classList.add("hidden");
    tSearch.className =
      "text-neutral-900 border-b-2 border-sky-500 pb-1 flex items-center gap-1.5 transition";
    tCreate.className =
      "text-neutral-400 hover:text-neutral-600 pb-1 flex items-center gap-1.5 transition";
  } else {
    aSearch.classList.add("hidden");
    aCreate.classList.remove("hidden");
    tCreate.className =
      "text-neutral-900 border-b-2 border-sky-500 pb-1 flex items-center gap-1.5 transition";
    tSearch.className =
      "text-neutral-400 hover:text-neutral-600 pb-1 flex items-center gap-1.5 transition";
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

// Updated preset handler to store the configuration choice
function applyPreset(tw) {
  const b = document.getElementById("canvasBody");
  b.style.backgroundImage = "";
  b.className =
    "min-h-screen md:h-screen flex flex-col p-4 max-w-5xl mx-auto w-full gap-4 md:overflow-hidden font-sans relative transition-all duration-300 pb-16 md:pb-4 " +
    tw;
  
  // Update the form tracking value securely before submission
  const paletteInput = document.getElementById("selectedPaletteInput");
  if (paletteInput) {
    paletteInput.value = tw;
  }
}

// Intercept Form Submissions to eliminate raw JSON drops
document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("nexusCreateArea");
  if (form) {
    form.addEventListener("submit", async (event) => {
      event.preventDefault(); // HALTS standard browser redirection loops

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
          // Relocate to global core workspace canvas route string
          window.location.href = "/group/" + data.group_id; 
        } else if (data.redirect_to) {
          // Redirect the guest straight to authentication screen
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

function togglePasswordField() {
  const securitySelect = document.getElementById("securityEngineSelect");
  const passwordContainer = document.getElementById("passwordContainer");
  const passwordInput = document.getElementById("groupPasswordInput");

  if (!securitySelect || !passwordContainer || !passwordInput) return;

  if (securitySelect.value === "secure") {
    // Show password field
    passwordContainer.classList.remove("hidden");
    passwordInput.required = true;
  } else {
    // Hide password field & reset input value
    passwordContainer.classList.add("hidden");
    passwordInput.required = false;
    passwordInput.value = "";
  }
}

// Ensure the initial state is synchronized on page load
document.addEventListener("DOMContentLoaded", () => {
  togglePasswordField();
});