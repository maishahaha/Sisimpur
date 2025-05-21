// Toast notification system
console.log("Toast.js loaded");
document.addEventListener("DOMContentLoaded", function () {
  console.log("Toast.js DOM ready");
  // Function to show a toast notification
  window.showToast = function (type, title, message) {
    console.log("Showing toast:", type, title, message);
    // Create toast elements
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;

    // Create header
    const header = document.createElement("div");
    header.className = "toast-header";

    // Create icon
    const icon = document.createElement("div");
    icon.className = "toast-icon";
    const iconI = document.createElement("i");

    if (type === "success") {
      iconI.className = "fas fa-check";
    } else if (type === "error") {
      iconI.className = "fas fa-exclamation";
    } else if (type === "warning") {
      iconI.className = "fas fa-bell";
    } else if (type === "info") {
      iconI.className = "fas fa-info";
    }

    icon.appendChild(iconI);

    // Create title
    const titleEl = document.createElement("h5");
    titleEl.className = "toast-title";
    titleEl.textContent = title;

    // Create close button
    const closeBtn = document.createElement("button");
    closeBtn.className = "toast-close";
    closeBtn.innerHTML = "&times;";
    closeBtn.onclick = function () {
      removeToast(toast);
    };

    // Create body
    const body = document.createElement("div");
    body.className = "toast-body";
    body.textContent = message;

    // Create progress
    const progress = document.createElement("div");
    progress.className = "toast-progress";
    const progressBar = document.createElement("div");
    progressBar.className = "toast-progress-bar";
    progress.appendChild(progressBar);

    // Assemble toast
    header.appendChild(icon);
    header.appendChild(titleEl);
    header.appendChild(closeBtn);

    toast.appendChild(header);
    toast.appendChild(body);
    toast.appendChild(progress);

    // Add to container
    const container = document.getElementById("toast-container");
    if (container) {
      container.appendChild(toast);

      // Auto remove after 5 seconds
      setTimeout(function () {
        removeToast(toast);
      }, 5000);
    } else {
      console.error("Toast container not found!");
    }
  };

  // Function to remove a toast with animation
  function removeToast(toast) {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    toast.style.transition = "all 0.3s ease";

    setTimeout(function () {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast);
      }
    }, 300);
  }

  // Process Django messages if they exist
  const djangoMessages = document.querySelectorAll(".django-message");
  djangoMessages.forEach(function (messageElement) {
    const type = messageElement.dataset.type;
    const title = messageElement.dataset.title || capitalizeFirstLetter(type);
    const message = messageElement.textContent.trim();

    if (message) {
      setTimeout(function () {
        showToast(type, title, message);
      }, 300); // Small delay to ensure DOM is ready

      // Remove the message element
      messageElement.remove();
    }
  });

  // Helper function to capitalize first letter
  function capitalizeFirstLetter(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
  }
});
