/**
 * SmartCivic Leaflet.js + OpenStreetMap Utilities
 */

// Haversine Distance calculation in kilometers
function calculateHaversineDistance(lat1, lon1, lat2, lon2) {
  const R = 6371; // Radius of Earth in km
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = 
    Math.sin(dLat/2) * Math.sin(dLat/2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
    Math.sin(dLon/2) * Math.sin(dLon/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return (R * c).toFixed(2); // returns string like "1.45"
}

// Global Map instances dictionary
const smartMaps = {};

function initLeafletMap(containerId, centerLat = 28.6139, centerLng = 77.2090, zoomLevel = 13) {
  const container = document.getElementById(containerId);
  if (!container) return null;

  if (smartMaps[containerId]) {
    smartMaps[containerId].remove();
  }

  const map = L.map(containerId).setView([centerLat, centerLng], zoomLevel);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(map);

  smartMaps[containerId] = map;
  return map;
}

// Marker helper with custom color icons
function createCustomIcon(colorHex, iconClass = "bi-geo-alt-fill") {
  return L.divIcon({
    className: 'custom-leaflet-marker',
    html: `<div style="
      background-color: ${colorHex};
      width: 32px;
      height: 32px;
      border-radius: 50%;
      border: 3px solid white;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      box-shadow: 0 4px 10px rgba(0,0,0,0.3);
      font-size: 16px;
    "><i class="bi ${iconClass}"></i></div>`,
    iconSize: [32, 32],
    iconAnchor: [16, 32],
    popupAnchor: [0, -32]
  });
}

// Render Safe Spots on map + sort list by nearest
async function loadAndRenderSafeSpots(mapContainerId, categoryFilter = "ALL") {
  const userLoc = await window.SmartLocation.getCurrentPosition();
  const map = initLeafletMap(mapContainerId, userLoc.latitude, userLoc.longitude, 13);
  if (!map) return;

  // Add user's location marker
  L.marker([userLoc.latitude, userLoc.longitude], {
    icon: createCustomIcon("#2563eb", "bi-person-fill")
  }).addTo(map).bindPopup("<b>Your Current Location</b>").openPopup();

  try {
    const response = await fetch("/api/safe-spots");
    const spots = await response.json();

    const listContainer = document.getElementById("safe-spots-list");
    if (listContainer) listContainer.innerHTML = "";

    // Calculate distance for all spots
    spots.forEach(spot => {
      spot.distanceKm = parseFloat(calculateHaversineDistance(
        userLoc.latitude, userLoc.longitude, spot.latitude, spot.longitude
      ));
    });

    // Sort by nearest first
    spots.sort((a, b) => a.distanceKm - b.distanceKm);

    let count = 0;
    spots.forEach(spot => {
      if (categoryFilter !== "ALL" && spot.spot_type.toLowerCase() !== categoryFilter.toLowerCase()) {
        return;
      }
      count++;

      // Pick icon color by type
      let color = "#10b981"; // emerald
      let icon = "bi-hospital";
      if (spot.spot_type === "Police Station") { color = "#3b82f6"; icon = "bi-shield-shaded"; }
      if (spot.spot_type === "Fire Station") { color = "#ef4444"; icon = "bi-fire"; }
      if (spot.spot_type === "Shelter") { color = "#f59e0b"; icon = "bi-house-heart"; }
      if (spot.spot_type === "Pharmacy") { color = "#8b5cf6"; icon = "bi-capsule"; }

      const marker = L.marker([spot.latitude, spot.longitude], {
        icon: createCustomIcon(color, icon)
      }).addTo(map);

      const popupContent = `
        <div style="min-width: 180px;">
          <h6 class="font-weight-bold mb-1" style="margin:0;">${spot.name}</h6>
          <small class="badge bg-secondary mb-2">${spot.spot_type}</small>
          <p style="font-size: 0.8rem; margin-bottom: 4px;">📍 ${spot.address}</p>
          <p style="font-size: 0.8rem; margin-bottom: 4px;">📞 ${spot.phone}</p>
          <strong style="color: #2563eb; font-size: 0.85rem;">Distance: ${spot.distanceKm} km</strong>
        </div>
      `;
      marker.bindPopup(popupContent);

      // Append to list if HTML element exists
      if (listContainer) {
        const card = document.createElement("div");
        card.className = "card mb-3 shadow-sm border-0 rounded-3";
        card.innerHTML = `
          <div class="card-body p-3 d-flex justify-content-between align-items-center">
            <div>
              <div class="d-flex align-items-center gap-2 mb-1">
                <h6 class="fw-bold mb-0">${spot.name}</h6>
                <span class="badge bg-light text-dark border">${spot.spot_type}</span>
              </div>
              <p class="text-muted small mb-1"><i class="bi bi-geo-alt"></i> ${spot.address}</p>
              <span class="fw-bold text-primary small"><i class="bi bi-pin-map"></i> ${spot.distanceKm} km away</span>
            </div>
            <button class="btn btn-outline-primary btn-sm rounded-pill px-3" onclick="focusOnMap(${spot.latitude}, ${spot.longitude}, '${mapContainerId}')">
              <i class="bi bi-map me-1"></i> View
            </button>
          </div>
        `;
        listContainer.appendChild(card);
      }
    });

    if (listContainer && count === 0) {
      listContainer.innerHTML = `<div class="text-center p-4 text-muted">No safety locations found for category '${categoryFilter}'.</div>`;
    }

  } catch (err) {
    console.error("Failed to load safe spots:", err);
  }
}

function focusOnMap(lat, lng, containerId) {
  const map = smartMaps[containerId];
  if (map) {
    map.setView([lat, lng], 16);
    // Smooth scroll to map
    document.getElementById(containerId)?.scrollIntoView({ behavior: 'smooth' });
  }
}
