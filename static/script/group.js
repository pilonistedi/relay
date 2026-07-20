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

// Function to fetch and render messages
async function fetchShoutboxMessages() {
  try {
    const response = await fetch(`/chat/${CURRENT_GROUP_ID}/messages`);
    if (!response.ok) return;
    
    const data = await response.json();
    const shoutboxContainer = document.getElementById('shoutboxMessages');
    
    // Clear previous static/dynamic messages
    shoutboxContainer.innerHTML = '';
    
    if (data.messages.length === 0) {
      shoutboxContainer.innerHTML = `
        <div class="text-center py-4 text-neutral-600 italic text-[11px]">
          No messages yet. Start the conversation!
        </div>
      `;
      return;
    }

    data.messages.forEach(msg => {
      const msgEl = document.createElement('div');
      msgEl.className = 'bg-neutral-950/60 p-2.5 rounded-xl border border-neutral-800/50 leading-relaxed transition-all';
      msgEl.innerHTML = `
        <div class="flex justify-between items-baseline mb-1">
          <span class="font-medium text-white flex items-center gap-1.5">
            <span class="text-xs">${msg.user_emoji || '👾'}</span>
            <strong class="text-sky-400">${msg.username}</strong>
          </span>
          <span class="text-[9px] text-neutral-500 font-mono">${msg.sent_at}</span>
        </div>
        <p class="text-neutral-300 break-words">${escapeHTML(msg.message_text)}</p>
      `;
      shoutboxContainer.appendChild(msgEl);
    });

    // Auto-scroll to the bottom of the shoutbox on update
    shoutboxContainer.scrollTop = shoutboxContainer.scrollHeight;
  } catch (error) {
    console.error('Error loading shoutbox logs:', error);
  }
}

// Function to safely send a shoutbox message
async function sendShoutboxMessage() {
  const inputEl = document.getElementById('shoutboxInput');
  const messageText = inputEl.value.trim();
  if (!messageText) return;

  // Clear input instantly for snappy UX feel
  inputEl.value = '';

  try {
    const response = await fetch(`/chat/${CURRENT_GROUP_ID}/send`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ message_text: messageText })
    });

    if (response.ok) {
      // Reload UI on immediate success
      fetchShoutboxMessages();
    } else {
      console.error('Failed to post message to chat log.');
    }
  } catch (error) {
    console.error('Error posting message:', error);
  }
}

// Simple HTML escaper helper to secure custom inputs from XSS
function escapeHTML(str) {
  return str.replace(/[&<>'"]/g, 
    tag => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      "'": '&#39;',
      '"': '&quot;'
    }[tag] || tag)
  );
}

// Set up the automatic live poller
document.addEventListener('DOMContentLoaded', () => {
  fetchShoutboxMessages();
  // Poll database for new squad chat logs every 4 seconds
  setInterval(fetchShoutboxMessages, 4000);
});

document.addEventListener('DOMContentLoaded', () => {
  const shoutboxContainer = document.getElementById('shoutboxMessages');
  if (shoutboxContainer) {
    // Scroll directly to the newest message on initial load
    shoutboxContainer.scrollTop = shoutboxContainer.scrollHeight;
  }
  
  // Keep live fetching active for updates every 4 seconds
  setInterval(fetchShoutboxMessages, 4000);
});

function deleteMyDrop(groupId, dropId) {
    if (!confirm("Are you sure you want to permanently delete this file?")) return;

    fetch(`/group/${groupId}/drop/${dropId}/delete`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            // Success: Reset the UI slot layout seamlessly back to the 
            // empty state with "Deploy Empty Path" visible!
            window.location.reload(); // Or target and clean the slot via DOM manipulation
        } else {
            alert(data.error);
        }
    })
    .catch(err => console.error("Deletion error:", err));
}

/**
 * Generic modal toggle helper
 * (If you already have toggleModal defined elsewhere, you can skip this definition)
 */
function toggleModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.toggle('hidden');
  }
}

/**
 * Close modal if clicking on the semi-transparent backdrop
 */
function handleBackdropClick(event, modalId) {
  if (event.target.id === modalId) {
    toggleModal(modalId);
  }
}

/**
 * Called when the Gear/Settings button is clicked on a Card Slot.
 * Fetches current data to prefill (or uses safe defaults) and opens the modal.
 */
function openCardSettings(dropId) {
  // Store the active drop ID in the hidden input field
  document.getElementById('cardSettingsId').value = dropId;

  // Optional: If you want to pre-fill current values from the clicked card
  // dynamically prior to sending updates, you can query your DOM or database.
  // For standard user experience, we clear or pull existing attributes:
  document.getElementById('cardNameInput').value = ""; 
  document.getElementById('cardEmojiInput').value = ""; 

  // Display the Card Settings modal
  toggleModal('cardSettingsModal');
}

/**
 * Submits the updated card configuration parameters to your backend API.
 */
function saveCardSettings() {
  const dropId = document.getElementById('cardSettingsId').value;
  const cardName = document.getElementById('cardNameInput').value;
  const cardEmoji = document.getElementById('cardEmojiInput').value;
  const cardColor = document.getElementById('cardColorInput').value;

  // Prepare data payload to synchronize with database back-end
  const payload = {
    original_name: cardName,
    user_emoji: cardEmoji,
    card_color: cardColor
  };

  // Adjust URL to match your server routing architecture (e.g., /group/<group_id>/drop/<drop_id>/update)
  fetch(`/api/drops/${dropId}/update`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  })
  .then(response => {
    if (response.ok) {
      // Reload page to securely render new states instantly
      window.location.reload();
    } else {
      alert("Failed to update card settings. Please try again.");
    }
  })
  .catch(err => {
    console.error("Error saving card configuration settings:", err);
    alert("An error occurred. Checking connection status.");
  });
}