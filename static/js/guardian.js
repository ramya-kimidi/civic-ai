/**
 * SmartCivic Guardian Journey Periodic Location Tracker & Public Tracker
 */

let journeyInterval = null;
let activeTrackingCode = null;

function initGuardianJourney() {
  const startForm = document.getElementById("guardian-start-form");
  const stopBtn = document.getElementById("reach-safely-btn");

  if (startForm) {
    startForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      const traveller_name = document.getElementById("traveller_name")?.value;
      const guardian_name = document.getElementById("guardian_name")?.value;
      const guardian_contact = document.getElementById("guardian_contact")?.value;
      const destination = document.getElementById("destination")?.value;
      const expected_arrival = document.getElementById("expected_arrival")?.value;

      const submitBtn = startForm.querySelector("button[type='submit']");
      if (submitBtn) submitBtn.disabled = true;

      const loc = await window.SmartLocation.getCurrentPosition();

      try {
        const response = await fetch("/api/journey/start", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            traveller_name,
            guardian_name,
            guardian_contact,
            destination,
            expected_arrival,
            latitude: loc.latitude,
            longitude: loc.longitude
          })
        });

        const data = await response.json();
        if (data.status === "success") {
          activeTrackingCode = data.tracking_code;

          // Show active journey state
          document.getElementById("journey-setup-card")?.classList.add("d-none");
          const activeCard = document.getElementById("journey-active-card");
          if (activeCard) {
            activeCard.classList.remove("d-none");
            document.getElementById("active-dest-text").innerText = destination;
            document.getElementById("active-code-text").innerText = data.tracking_code;
            
            const shareLinkInput = document.getElementById("share-link-input");
            if (shareLinkInput) {
              shareLinkInput.value = window.location.origin + data.tracking_url;
            }
          }

          // Start periodic GPS heartbeat every 15 seconds
          startPeriodicLocationUpdates(data.tracking_code);
        }
      } catch (err) {
        alert("Failed to start journey. Check connection.");
      } finally {
        if (submitBtn) submitBtn.disabled = false;
      }
    });
  }

  if (stopBtn) {
    stopBtn.addEventListener("click", async () => {
      if (!activeTrackingCode) return;

      try {
        const res = await fetch("/api/journey/complete", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ tracking_code: activeTrackingCode })
        });
        const data = await res.json();
        clearInterval(journeyInterval);

        alert(data.message);
        window.location.reload();
      } catch (err) {
        alert("Error marking journey complete.");
      }
    });
  }
}

function startPeriodicLocationUpdates(code) {
  clearInterval(journeyInterval);
  journeyInterval = setInterval(async () => {
    const loc = await window.SmartLocation.getCurrentPosition();
    fetch("/api/journey/location", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        tracking_code: code,
        latitude: loc.latitude,
        longitude: loc.longitude
      })
    }).then(res => res.json()).then(data => {
      console.log("Guardian GPS heartbeat updated:", data);
      const lastUpdateText = document.getElementById("last-gps-time");
      if (lastUpdateText) lastUpdateText.innerText = new Date().toLocaleTimeString();
    }).catch(console.error);
  }, 15000);
}

function copyShareLink() {
  const input = document.getElementById("share-link-input");
  if (input) {
    input.select();
    navigator.clipboard.writeText(input.value);
    alert("Tracking link copied to clipboard! Share this with your guardian.");
  }
}

document.addEventListener("DOMContentLoaded", initGuardianJourney);
