// Extract Group ID dynamically from the URL path (e.g., /group/12 => 12)
const pathParts = window.location.pathname.split('/');
const groupIndex = pathParts.indexOf('group');
const groupId = groupIndex !== -1 ? pathParts[groupIndex + 1] : null;

/**
 * -------------------------------------------------------------
 * 1. Modal Toggle Handlers
 * -------------------------------------------------------------
 */
function toggleModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.toggle('hidden');
  }
}

function handleBackdropClick(event, modalId) {
  // Only close if the background/overlay itself was clicked, not the inner container
  if (event.target === event.currentTarget) {
    toggleModal(modalId);
  }
}

/**
 * -------------------------------------------------------------
 * 2. File Upload Infrastructure (AJAX with upload.py)
 * -------------------------------------------------------------
 */

// Triggered by the "Add Card" button
function handleAddCard() {
  const globalInput = document.getElementById('globalFileInput');
  if (globalInput) {
    globalInput.click();
  }
}

// Triggered by the change event of the global file input
function handleGlobalFileSelect(input) {
  if (input.files && input.files[0]) {
    uploadFile(input.files[0]);
  }
}

/**
 * Sends file to the backend @group_handler_bp.route("/group/<int:group_id>/upload")[cite: 2]
 */
async function uploadFile(file) {
  if (!groupId) {
    showToast("Error: Workspace context group ID could not be detected.", "error");
    return;
  }

  // Visual uploading indicator (optional placeholder for user experience)
  showToast(`Uploading "${file.name}"...`, "info");

  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await fetch(`/group/${groupId}/upload`, {
      method: 'POST',
      body: formData
    });

    const result = await response.json();

    if (response.ok && result.success) {
      showToast(`Successfully ${result.action} file: ${result.original_name}`, "success");
      
      // Auto-reload the workspace to show the newly populated grid slots
      setTimeout(() => {
        window.location.reload();
      }, 1000);
    } else {
      showToast(result.error || "Upload failed. Please try again.", "error");
    }
  } catch (error) {
    console.error("Upload error:", error);
    showToast("Server connection error during upload.", "error");
  }
}

/**
 * -------------------------------------------------------------
 * 3. Event Listeners & Drag-And-Drop Watchers
 * -------------------------------------------------------------
 */
document.addEventListener('DOMContentLoaded', () => {
  // Dynamic watcher for the Auto-Allocate Dropzone input trigger
  const globalDropZone = document.getElementById('globalDropZone');
  if (globalDropZone) {
    globalDropZone.addEventListener('change', (e) => {
      if (e.target.files && e.target.files[0]) {
        uploadFile(e.target.files[0]);
      }
    });
  }

  // Watcher for any empty slot file inputs
  document.querySelectorAll('input[type="file"]').forEach(input => {
    if (input.id !== 'globalFileInput' && input.id !== 'globalDropZone') {
      input.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0]) {
          uploadFile(e.target.files[0]);
        }
      });
    }
  });
});

/**
 * -------------------------------------------------------------
 * 4. Settings Configuration Endpoint Integration
 * -------------------------------------------------------------
 */
async function saveSystemConfig() {
  const lifespanInput = document.getElementById('lifespanInput');
  if (!lifespanInput) return;

  const newLifespan = parseInt(lifespanInput.value, 10);
  if (isNaN(newLifespan) || newLifespan < 1) {
    showToast("Please enter a valid timeframe in minutes.", "error");
    return;
  }

  try {
    // Assuming a standard configuration update route on your backend
    const response = await fetch(`/group/${groupId}/config`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ lifespan_minutes: newLifespan })
    });

    if (response.ok) {
      showToast("System configurations saved successfully!", "success");
      toggleModal('adminModal');
      
      // Update displayed state
      const globalDisplay = document.getElementById('globalLifesDisplay');
      if (globalDisplay) {
        globalDisplay.textContent = `${newLifespan}m limit`;
      }
    } else {
      const data = await response.json();
      showToast(data.error || "Failed to update backend system configuration.", "error");
    }
  } catch (err) {
    console.error(err);
    showToast("Network failure saving settings.", "error");
  }
}

/**
 * -------------------------------------------------------------
 * 5. Shoutbox Messaging System
 * -------------------------------------------------------------
 */
function sendShoutboxMessage() {
  const input = document.getElementById('shoutboxInput');
  if (!input || !input.value.trim()) return;

  const messageText = input.value.trim();
  
  // 1. Append immediately to UI for dynamic feel
  appendLocalMessage(messageText);
  input.value = '';

  // 2. Dispatch to backend (Implement /group/<id>/shout route if desired)
  fetch(`/group/${groupId}/shout`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: messageText })
  }).catch(err => console.warn("Failed syncing shout message to server database trace.", err));
}

function appendLocalMessage(text) {
  const container = document.getElementById('shoutboxMessages');
  if (!container) return;

  const now = new Date();
  const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  const messageWrapper = document.createElement('div');
  messageWrapper.className = "bg-neutral-950/60 p-2.5 rounded-xl border border-neutral-800/50 leading-relaxed animate-fade-in";
  messageWrapper.innerHTML = `
    <div class="flex justify-between items-baseline mb-1">
      <strong class="text-sky-400 font-medium">You</strong>
      <span class="text-[9px] text-neutral-500 font-mono">${timeStr}</span>
    </div>
    <p class="text-neutral-300">${escapeHTML(text)}</p>
  `;

  container.appendChild(messageWrapper);
  container.scrollTop = container.scrollHeight;
}

/**
 * -------------------------------------------------------------
 * 6. Helper Utilities
 * -------------------------------------------------------------
 */
function escapeHTML(str) {
  return str.replace(/[&<>'"]/g, 
    tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
  );
}

// Simple absolute banner toast system to communicate events elegantly without interrupting alerts
function showToast(message, type = "info") {
  let toast = document.getElementById("relay-toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "relay-toast";
    toast.className = "fixed top-6 right-6 z-50 px-4 py-3 rounded-xl shadow-2xl text-xs font-semibold tracking-wide transition-all duration-300 transform translate-y-[-20px] opacity-0 border";
    document.body.appendChild(toast);
  }

  // Clean transitions
  toast.classList.remove("opacity-100", "translate-y-0");
  toast.classList.add("opacity-0", "translate-y-[-20px]");

  setTimeout(() => {
    // Coloring
    if (type === "success") {
      toast.className = "fixed top-6 right-6 z-50 px-4 py-3 rounded-xl shadow-2xl text-xs font-semibold tracking-wide transition-all duration-300 bg-emerald-950/90 text-emerald-400 border-emerald-500/20";
    } else if (type === "error") {
      toast.className = "fixed top-6 right-6 z-50 px-4 py-3 rounded-xl shadow-2xl text-xs font-semibold tracking-wide transition-all duration-300 bg-red-950/90 text-red-400 border-red-500/20";
    } else {
      toast.className = "fixed top-6 right-6 z-50 px-4 py-3 rounded-xl shadow-2xl text-xs font-semibold tracking-wide transition-all duration-300 bg-neutral-900/90 text-neutral-200 border-neutral-800";
    }

    toast.innerText = message;
    toast.classList.remove("opacity-0", "translate-y-[-20px]");
    toast.classList.add("opacity-100", "translate-y-0");
  }, 100);

  // Auto-dismiss
  setTimeout(() => {
    toast.classList.remove("opacity-100", "translate-y-0");
    toast.classList.add("opacity-0", "translate-y-[-20px]");
  }, 4000);
}