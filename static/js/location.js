/**
 * SmartCivic Geolocation Helper Script
 * Wraps Navigator.geolocation with fallback support, simulation override, and live position change events.
 */

window.SmartLocation = {
  // Default fallback coordinates (New Delhi / Metropolitan Center)
  DEFAULT_LAT: 28.6139,
  DEFAULT_LNG: 77.2090,

  PRESETS: {
    downtown: { name: "Downtown / Civic Center", lat: 28.6139, lng: 77.2090 },
    north: { name: "North Sector / Precinct 5", lat: 28.6280, lng: 77.2180 },
    hospital: { name: "Metro Hospital Medical Zone", lat: 28.6100, lng: 77.2000 },
    flood: { name: "South Sector Lowlands (Flood Zone)", lat: 28.6010, lng: 77.2150 },
    industrial: { name: "West End Industrial Park", lat: 28.6320, lng: 77.1950 }
  },

  // Get current active position (checking simulated override first)
  getCurrentPosition: function() {
    return new Promise((resolve) => {
      // 1. Check if user set a simulated live location
      const sim = localStorage.getItem("smartcivic_sim_loc");
      if (sim) {
        try {
          const parsed = JSON.parse(sim);
          resolve({
            latitude: parseFloat(parsed.lat),
            longitude: parseFloat(parsed.lng),
            label: parsed.name || "Simulated Location",
            isSimulated: true,
            isFallback: false
          });
          return;
        } catch (e) {
          localStorage.removeItem("smartcivic_sim_loc");
        }
      }

      // 2. Try native browser geolocation
      if (!navigator.geolocation) {
        resolve({
          latitude: this.DEFAULT_LAT,
          longitude: this.DEFAULT_LNG,
          label: "City Center (Default)",
          isSimulated: false,
          isFallback: true
        });
        return;
      }

      navigator.geolocation.getCurrentPosition(
        (position) => {
          resolve({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy,
            label: "GPS Live Location",
            isSimulated: false,
            isFallback: false
          });
        },
        (error) => {
          resolve({
            latitude: this.DEFAULT_LAT,
            longitude: this.DEFAULT_LNG,
            label: "City Center (Fallback)",
            isSimulated: false,
            isFallback: true,
            error: error.message
          });
        },
        {
          enableHighAccuracy: true,
          timeout: 8000,
          maximumAge: 0
        }
      );
    });
  },

  // Set a simulated location override
  setSimulatedLocation: async function(lat, lng, name = "Custom Location") {
    const data = { lat: parseFloat(lat), lng: parseFloat(lng), name: name };
    localStorage.setItem("smartcivic_sim_loc", JSON.stringify(data));
    
    // Broadcast change event
    window.dispatchEvent(new CustomEvent("smartcivic:location-changed", { detail: data }));
    
    // Update global UI displays
    this.updateLocationDisplay();
    return data;
  },

  // Reset to default/GPS
  clearSimulatedLocation: async function() {
    localStorage.removeItem("smartcivic_sim_loc");
    window.dispatchEvent(new CustomEvent("smartcivic:location-changed", { detail: null }));
    this.updateLocationDisplay();
  },

  // Update header bar location text
  updateLocationDisplay: async function() {
    const loc = await this.getCurrentPosition();
    const displayEl = document.getElementById("global-location-display");
    if (displayEl) {
      const simTag = loc.isSimulated ? ` <span class="badge bg-warning text-dark ms-1">Simulated</span>` : "";
      displayEl.innerHTML = `<i class="bi bi-geo-alt-fill text-danger me-1"></i> <strong>${loc.label}</strong> (${loc.latitude.toFixed(4)}, ${loc.longitude.toFixed(4)})${simTag}`;
    }

    // Auto update hidden lat/lng inputs in forms if present
    const latInputs = document.querySelectorAll("input[name='latitude'], #disaster_lat, #user_lat");
    const lngInputs = document.querySelectorAll("input[name='longitude'], #disaster_lng, #user_lng");
    latInputs.forEach(i => i.value = loc.latitude.toFixed(4));
    lngInputs.forEach(i => i.value = loc.longitude.toFixed(4));
  },

  // Trigger Emergency SOS API Call
  triggerSOS: async function(notes = "Emergency SOS Alert") {
    const loc = await this.getCurrentPosition();
    try {
      const response = await fetch("/api/sos", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          latitude: loc.latitude,
          longitude: loc.longitude,
          notes: notes,
          address: loc.isSimulated ? `${loc.label} (Simulated)` : `GPS Location: ${loc.latitude.toFixed(4)}, ${loc.longitude.toFixed(4)}`
        })
      });
      const data = await response.json();
      return data;
    } catch (err) {
      console.error("SOS Fetch Error:", err);
      return { status: "error", message: "Network or server connection failed." };
    }
  }
};

// Initialize location display on DOM Ready
document.addEventListener("DOMContentLoaded", () => {
  SmartLocation.updateLocationDisplay();
});

// Modal Helper Functions for Location Control Widget
async function applyPresetLocation(lat, lng, label) {
  await SmartLocation.setSimulatedLocation(lat, lng, label);
  closeLocationModalAndReload();
}

async function applyCustomLocation() {
  const lat = document.getElementById("custom_sim_lat")?.value;
  const lng = document.getElementById("custom_sim_lng")?.value;
  if (!lat || !lng) {
    alert("Please enter both valid Latitude and Longitude values.");
    return;
  }
  await SmartLocation.setSimulatedLocation(lat, lng, "Custom Coordinates");
  closeLocationModalAndReload();
}

async function resetBrowserLocation() {
  await SmartLocation.clearSimulatedLocation();
  closeLocationModalAndReload();
}

function closeLocationModalAndReload() {
  const modalEl = document.getElementById("locationModal");
  if (modalEl) {
    const modal = bootstrap.Modal.getInstance(modalEl);
    if (modal) modal.hide();
  }
  // Refresh safe spots or page maps if present
  if (typeof loadAndRenderSafeSpots === "function") {
    loadAndRenderSafeSpots("map");
  }
  // Trigger general reload or map re-initialization
  window.location.reload();
}


