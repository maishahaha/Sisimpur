// Simple Toast Notification System
console.log("Toast_new.js loaded");

// Wait for DOM to be fully loaded
document.addEventListener("DOMContentLoaded", function () {
  console.log("Toast_new.js DOM ready");

  // Check if toast container exists, create one if it doesn't
  let toastContainer = document.getElementById("toast-container");
  if (!toastContainer) {
    console.log("Creating toast container");
    toastContainer = document.createElement("div");
    toastContainer.id = "toast-container";
    toastContainer.style.position = "fixed";
    toastContainer.style.top = "20px";
    toastContainer.style.right = "20px";
    toastContainer.style.zIndex = "9999";
    toastContainer.style.width = "350px";
    document.body.appendChild(toastContainer);
  } else {
    console.log("Toast container found");
  }

  // Define the showToast function in the global scope
  window.showToast = function (type, title, message) {
    console.log("Showing toast:", type, title, message);

    // Create toast element
    const toast = document.createElement("div");
    toast.className = "toast-notification";
    toast.style.backgroundColor = "rgba(30, 30, 50, 0.9)";
    toast.style.color = "white";
    toast.style.borderRadius = "10px";
    toast.style.boxShadow = "0 4px 12px rgba(0, 0, 0, 0.3)";
    toast.style.overflow = "hidden";
    toast.style.marginBottom = "15px";
    toast.style.animation = "slideIn 0.3s ease forwards";

    // Set border color based on type
    let borderColor = "#3b82f6"; // Default blue for info
    let iconClass = "fa-info";

    if (type === "success") {
      borderColor = "#10b981"; // Green
      iconClass = "fa-check";
    } else if (type === "error") {
      borderColor = "#ef4444"; // Red
      iconClass = "fa-exclamation";
    } else if (type === "warning") {
      borderColor = "#f59e0b"; // Orange
      iconClass = "fa-bell";
    }

    toast.style.borderLeft = `4px solid ${borderColor}`;

    // Create toast content
    toast.innerHTML = `
            <div style="display: flex; align-items: center; padding: 12px 15px; background: rgba(0, 0, 0, 0.2);">
                <div style="width: 24px; height: 24px; background-color: ${borderColor}; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 10px;">
                    <i class="fas ${iconClass}" style="font-size: 12px;"></i>
                </div>
                <h5 style="margin: 0; flex-grow: 1; font-weight: 600;">${title}</h5>
                <button style="background: transparent; border: none; color: white; font-size: 18px; cursor: pointer; opacity: 0.7;" onclick="this.parentNode.parentNode.remove();">&times;</button>
            </div>
            <div style="padding: 15px;">${message}</div>
            <div style="height: 3px; background: rgba(255, 255, 255, 0.1); position: relative;">
                <div style="height: 100%; width: 100%; background-color: ${borderColor}; animation: progress 5s linear forwards;"></div>
            </div>
        `;

    // Add to container
    toastContainer.appendChild(toast);

    // Auto remove after 5 seconds
    setTimeout(function () {
      if (toast.parentNode) {
        toast.style.opacity = "0";
        toast.style.transform = "translateX(100%)";
        toast.style.transition = "all 0.3s ease";

        setTimeout(function () {
          if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
          }
        }, 300);
      }
    }, 5000);
  };

  // Add CSS for animations
  const style = document.createElement("style");
  style.textContent = `
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        @keyframes progress {
            from { width: 100%; }
            to { width: 0%; }
        }
    `;
  document.head.appendChild(style);

  // Process Django messages if they exist
  const djangoMessages = document.querySelectorAll(".django-message");
  djangoMessages.forEach(function (messageElement) {
    const type = messageElement.dataset.type;
    const title = messageElement.dataset.title || capitalizeFirstLetter(type);
    const message = messageElement.textContent.trim();

    if (message) {
      setTimeout(function () {
        window.showToast(type, title, message);
      }, 300);

      // Remove the message element
      messageElement.remove();
    }
  });

  // Helper function to capitalize first letter
  function capitalizeFirstLetter(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
  }
});
