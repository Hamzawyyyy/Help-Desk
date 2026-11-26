// Member 1 — shared browser behaviour

// Ask for confirmation before submitting any form with data-confirm="message".
document.addEventListener("submit", function (event) {
  const message = event.target.getAttribute("data-confirm");
  if (message && !window.confirm(message)) {
    event.preventDefault();
  }
});

// Fade out success messages after 4 seconds.
setTimeout(function () {
  document.querySelectorAll(".alert-success").forEach(function (alert) {
    alert.classList.remove("show");
  });
}, 4000);