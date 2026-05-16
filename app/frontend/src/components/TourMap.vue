<script setup lang="ts">
import { ref, watch, computed, onMounted, onUnmounted, nextTick } from "vue";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

const props = defineProps<{
  waypoints: [number, number][];
  routes: [number, number][][];
  pois: { lat: number; lon: number; name: string; category?: string }[];
  elevation: [number, number][];
}>();

const mapContainer = ref<HTMLElement | null>(null);
let map: L.Map | null = null;
let routeLayers: L.Polyline[] = [];
let markerLayer: L.LayerGroup | null = null;
let poiLayer: L.LayerGroup | null = null;
let resizeObserver: ResizeObserver | null = null;

function initMap() {
  if (!mapContainer.value || map) return;
  map = L.map(mapContainer.value).setView([52.5, 13.4], 7);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    maxZoom: 18,
  }).addTo(map);
  markerLayer = L.layerGroup().addTo(map);
  poiLayer = L.layerGroup().addTo(map);

  // Invalidate map size when container resizes (split-pane drag)
  resizeObserver = new ResizeObserver(() => {
    map?.invalidateSize();
  });
  resizeObserver.observe(mapContainer.value);
}

function addLegend() {
  if (!map) return;
  // Remove existing legend if any
  map.getContainer().querySelector(".map-legend")?.remove();

  if (props.pois.length === 0) return;

  const legend = new L.Control({ position: "bottomright" });
  legend.onAdd = () => {
    const div = L.DomUtil.create("div", "map-legend");
    div.style.cssText =
      "background:rgba(255,255,255,0.92);padding:6px 10px;border-radius:6px;font-size:13px;line-height:1.5;box-shadow:0 1px 4px rgba(0,0,0,0.15);";

    const categories = new Set(
      props.pois.map((p) => p.category).filter(Boolean),
    );
    const entries: [string, string, string][] = [];
    if (
      categories.has("museum") ||
      categories.has("castle") ||
      categories.has("memorial") ||
      categories.has("ruins") ||
      categories.has("church") ||
      categories.has("viewpoint")
    )
      entries.push(["#8b5cf6", "●", "Sehenswürdigkeiten"]);
    if (categories.has("artwork") || categories.has("gallery"))
      entries.push(["#ec4899", "●", "Kunst"]);
    if (
      categories.has("beer_garden") ||
      categories.has("cafe") ||
      categories.has("restaurant")
    )
      entries.push(["#f59e0b", "●", "Einkehr"]);
    if (categories.has("swimming"))
      entries.push(["#06b6d4", "●", "Badestellen"]);
    if (
      categories.has("bicycle_repair") ||
      categories.has("drinking_water") ||
      categories.has("picnic")
    )
      entries.push(["#10b981", "●", "Service"]);

    if (entries.length === 0) return div;

    div.innerHTML = entries
      .map(
        ([color, , label]) =>
          `<span style="color:${color};font-size:20px;vertical-align:middle">●</span> ${label}`,
      )
      .join("<br>");
    return div;
  };
  legend.addTo(map);
}

function poiColor(category?: string): string {
  switch (category) {
    case "beer_garden":
    case "cafe":
    case "restaurant":
      return "#f59e0b"; // amber — food/drink
    case "museum":
    case "castle":
    case "memorial":
    case "ruins":
    case "church":
    case "viewpoint":
      return "#8b5cf6"; // purple — sights
    case "artwork":
    case "gallery":
      return "#ec4899"; // pink — art
    case "swimming":
      return "#06b6d4"; // cyan — water
    case "bicycle_repair":
    case "drinking_water":
    case "picnic":
      return "#10b981"; // green — services
    default:
      return "#f59e0b"; // amber fallback
  }
}

function updateMap() {
  if (!map) return;

  // Clear previous layers
  routeLayers.forEach((layer) => map!.removeLayer(layer));
  routeLayers = [];
  if (markerLayer) {
    markerLayer.clearLayers();
  }
  if (poiLayer) {
    poiLayer.clearLayers();
  }

  const bounds: L.LatLngExpression[] = [];

  // Draw all route polylines
  for (const route of props.routes) {
    if (route.length > 1) {
      const latLngs = route.map(
        ([lat, lng]) => [lat, lng] as L.LatLngExpression,
      );
      const polyline = L.polyline(latLngs, {
        color: "#2563eb",
        weight: 4,
        opacity: 0.8,
      }).addTo(map);
      routeLayers.push(polyline);
      bounds.push(...latLngs);
    }
  }

  // Add waypoint markers
  if (props.waypoints.length > 0) {
    props.waypoints.forEach(([lat, lng], i) => {
      const marker = L.circleMarker([lat, lng], {
        radius: 8,
        fillColor:
          i === 0
            ? "#16a34a"
            : i === props.waypoints.length - 1
              ? "#dc2626"
              : "#2563eb",
        color: "#fff",
        weight: 2,
        fillOpacity: 0.9,
      });
      markerLayer?.addLayer(marker);
      bounds.push([lat, lng]);
    });
  }

  // Add POI markers with tooltips (colored by category)
  if (props.pois.length > 0) {
    props.pois.forEach((poi) => {
      const color = poiColor(poi.category);
      const marker = L.circleMarker([poi.lat, poi.lon], {
        radius: 8,
        fillColor: color,
        color: "#fff",
        weight: 1.5,
        fillOpacity: 0.9,
      });
      if (poi.name) {
        marker.bindTooltip(poi.name, {
          direction: "top",
          offset: [0, -6],
        });
      }
      poiLayer?.addLayer(marker);
      bounds.push([poi.lat, poi.lon]);
    });
  }

  // Fit bounds
  if (bounds.length > 0) {
    map.fitBounds(L.latLngBounds(bounds), { padding: [30, 30] });
  }

  // Update legend based on current POI categories
  addLegend();
}

onMounted(() => {
  nextTick(() => {
    initMap();
    updateMap();
  });
});

onUnmounted(() => {
  resizeObserver?.disconnect();
  map?.remove();
  map = null;
});

watch(
  [() => props.waypoints, () => props.routes, () => props.pois],
  () => {
    nextTick(() => {
      if (!map) initMap();
      updateMap();
    });
  },
  { deep: true },
);

// Elevation profile as SVG path
const elevationPath = computed(() => {
  if (props.elevation.length < 2) return "";
  const data = props.elevation;
  const maxDist = data[data.length - 1][0];
  const elevations = data.map((d) => d[1]);
  const minEle = Math.min(...elevations);
  const maxEle = Math.max(...elevations);
  const eleRange = maxEle - minEle || 1;

  const w = 100; // viewBox width percentage
  const h = 100; // viewBox height percentage
  const padding = 5;

  const points = data.map(([dist, ele]) => {
    const x = (dist / maxDist) * (w - padding);
    const y = h - padding - ((ele - minEle) / eleRange) * (h - 2 * padding);
    return `${x},${y}`;
  });

  return `M${points.join(" L")}`;
});

const elevationFill = computed(() => {
  if (props.elevation.length < 2) return "";
  const data = props.elevation;
  const maxDist = data[data.length - 1][0];
  const elevations = data.map((d) => d[1]);
  const minEle = Math.min(...elevations);
  const maxEle = Math.max(...elevations);
  const eleRange = maxEle - minEle || 1;

  const w = 100;
  const h = 100;
  const padding = 5;

  const points = data.map(([dist, ele]) => {
    const x = (dist / maxDist) * (w - padding);
    const y = h - padding - ((ele - minEle) / eleRange) * (h - 2 * padding);
    return `${x},${y}`;
  });

  const lastX = (maxDist / maxDist) * (w - padding);
  return `M0,${h - padding} L${points.join(" L")} L${lastX},${h - padding} Z`;
});

const elevationStats = computed(() => {
  if (props.elevation.length < 2) return null;
  const elevations = props.elevation.map((d) => d[1]);
  const totalDist = props.elevation[props.elevation.length - 1][0];
  return {
    min: Math.round(Math.min(...elevations)),
    max: Math.round(Math.max(...elevations)),
    dist: totalDist.toFixed(1),
  };
});
</script>

<template>
  <div class="bg-white rounded-lg shadow overflow-hidden h-full flex flex-col">
    <div ref="mapContainer" class="flex-1 min-h-0"></div>
    <div
      v-if="elevation.length >= 2"
      class="shrink-0 border-t border-gray-200 px-3 pt-2 pb-3"
    >
      <div class="flex items-center justify-between text-xs text-gray-500 mb-1">
        <span>{{ elevationStats?.min }} m</span>
        <span class="font-medium text-gray-700">Höhenprofil</span>
        <span>{{ elevationStats?.max }} m</span>
      </div>
      <svg viewBox="0 0 100 100" preserveAspectRatio="none" class="w-full h-14">
        <path :d="elevationFill" fill="#dbeafe" />
        <path
          :d="elevationPath"
          fill="none"
          stroke="#2563eb"
          stroke-width="0.8"
        />
      </svg>
      <div class="flex justify-between text-xs text-gray-400 mt-1">
        <span>0 km</span>
        <span>{{ elevationStats?.dist }} km</span>
      </div>
    </div>
  </div>
</template>
