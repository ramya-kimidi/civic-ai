/**
 * SmartCivic Accident Detection Logic
 * Uses DeviceMotion API and threshold detection + simulation trigger.
 */

let accidentTimer = null;
let countdownVal = 10;
let isMonitoring = false;
let accelerationThreshold = 22.0; // m/s^2 impact threshold

function initAccidentDetection() {
  const startBtn = document.getElementById("start-detection-btn");
  const simBtn = document.getElementById("simulate-accident-btn");
  const statusBadge = document.getElementById("monitoring-status");

  if (startBtn) {
    startBtn.addEventListener("click", () => {
      if (!isMonitoring) {
        startMonitoring();
      } else {
        stopMonitoring();
      }
    });
  }

  if (simBtn) {
    simBtn.addEventListener("click", () => {
      triggerAccidentSequence("Simulated Crash Impact Triggered");
    });
  }
}

function startMonitoring() {
  if (typeof DeviceMotionEvent !== "undefined" && typeof DeviceMotionEvent.requestPermission === "function") {
    DeviceMotionEvent.requestPermission().then(response => {
      if (response === "granted") {
        window.addEventListener("devicemotion", handleMotion);
        setMonitoringUI(true);
      } else {
        alert("Motion permission denied. You can still use the 'Simulate Accident' feature.");
      }
    }).catch(console.error);
  } else if ("DeviceMotionEvent" in window) {
    window.addEventListener("devicemotion", handleMotion);
    setMonitoringUI(true);
  } else {
    alert("DeviceMotion API not supported on this browser. You can use 'Simulate Accident' mode for testing.");
  }
}

function stopMonitoring() {
  window.removeEventListener("devicemotion", handleMotion);
  setMonitoringUI(false);
}

function setMonitoringUI(active) {
  isMonitoring = active;
  const startBtn = document.getElementById("start-detection-btn");
  const statusBadge = document.getElementById("monitoring-status");

  if (active) {
    if (startBtn) {
      startBtn.classList.replace("btn-primary", "btn-warning");
      startBtn.innerHTML = '<i class="bi bi-stop-circle me-1"></i> Stop Monitoring';
    }
    if (statusBadge) {
      statusBadge.className = "badge bg-success p-2";
      statusBadge.innerHTML = '<i class="bi bi-shield-check me-1"></i> Active Accelerometer Monitoring';
    }
  } else {
    if (startBtn) {
      startBtn.classList.replace("btn-warning", "btn-primary");
      startBtn.innerHTML = '<i class="bi bi-play-circle me-1"></i> Start Accident Detection';
    }
    if (statusBadge) {
      statusBadge.className = "badge bg-secondary p-2";
      statusBadge.innerHTML = '<i class="bi bi-pause-circle me-1"></i> Inactive';
    }
  }
}

function handleMotion(event) {
  if (!isMonitoring) return;
  const acc = event.accelerationIncludingGravity;
  if (!acc) return;

  const totalAcc = Math.sqrt((acc.x || 0) ** 2 + (acc.y || 0) ** 2 + (acc.z || 0) ** 2);
  if (totalAcc > accelerationThreshold) {
    stopMonitoring();
    triggerAccidentSequence(`Sudden Accelerometer Surge Detected (${totalAcc.toFixed(1)} m/s²)`);
  }
}

function triggerAccidentSequence(reasonStr) {
  countdownVal = 10;
  const modalEl = document.getElementById("accidentModal");
  const countdownEl = document.getElementById("countdown-timer");
  const reasonText = document.getElementById("accident-reason");

  if (reasonText) reasonText.innerText = reasonStr;
  if (countdownEl) countdownEl.innerText = countdownVal;

  const bsModal = new bootstrap.Modal(modalEl);
  bsModal.show();

  clearInterval(accidentTimer);
  accidentTimer = setInterval(() => {
    countdownVal--;
    if (countdownEl) countdownEl.innerText = countdownVal;

    if (countdownVal <= 0) {
      clearInterval(accidentTimer);
      bsModal.hide();
      dispatchAccidentAlert(reasonStr);
    }
  }, 1000);

  // Setup button handlers
  const safeBtn = document.getElementById("im-safe-btn");
  const helpBtn = document.getElementById("get-help-btn");

  if (safeBtn) {
    safeBtn.onclick = () => {
      clearInterval(accidentTimer);
      bsModal.hide();
      alert("Emergency cancelled. Glad you are safe!");
    };
  }

  if (helpBtn) {
    helpBtn.onclick = () => {
      clearInterval(accidentTimer);
      bsModal.hide();
      dispatchAccidentAlert(reasonStr + " (Manual 'Get Help' pressed)");
    };
  }
}

async function dispatchAccidentAlert(sensorReason) {
  const resultDiv = document.getElementById("accident-result");
  if (resultDiv) {
    resultDiv.innerHTML = `
      <div class="alert alert-info d-flex align-items-center">
        <div class="spinner-border spinner-border-sm me-2" role="status"></div>
        Getting GPS coordinates and notifying emergency response team...
      </div>
    `;
  }

  const loc = await window.SmartLocation.getCurrentPosition();

  try {
    const res = await fetch("/api/accident-alert", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        latitude: loc.latitude,
        longitude: loc.longitude,
        sensor_data: sensorReason
      })
    });
    const data = await res.json();

    if (resultDiv) {
      resultDiv.innerHTML = `
        <div class="alert alert-danger shadow-sm border-2 border-danger">
          <h5 class="alert-heading font-weight-bold mb-1"><i class="bi bi-exclamation-triangle-fill me-1"></i> Emergency Dispatched!</h5>
          <p class="mb-1">${data.message}</p>
          <hr class="my-2">
          <small class="text-muted">Captured Coordinates: ${loc.latitude.toFixed(4)}, ${loc.longitude.toFixed(4)}</small>
        </div>
      `;
    }
  } catch (err) {
    if (resultDiv) {
      resultDiv.innerHTML = `<div class="alert alert-warning">Error sending alert. Please call emergency services directly.</div>`;
    }
  }
}

document.addEventListener("DOMContentLoaded", initAccidentDetection);
