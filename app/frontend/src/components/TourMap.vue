<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, nextTick } from "vue";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

const props = defineProps<{
  waypoints: [number, number][];
  routes: [number, number][][];
}>();

const mapContainer = ref<HTMLElement | null>(null);
let map: L.Map | null = null;
let routeLayers: L.Polyline[] = [];
let markerLayer: L.LayerGroup | null = null;
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

  // Invalidate map size when container resizes (split-pane drag)
  resizeObserver = new ResizeObserver(() => {
    map?.invalidateSize();
  });
  resizeObserver.observe(mapContainer.value);
}

function updateMap() {
  if (!map) return;

  // Clear previous layers
  routeLayers.forEach((layer) => map!.removeLayer(layer));
  routeLayers = [];
  if (markerLayer) {
    markerLayer.clearLayers();
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

  // Fit bounds
  if (bounds.length > 0) {
    map.fitBounds(L.latLngBounds(bounds), { padding: [30, 30] });
  }
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
  [() => props.waypoints, () => props.routes],
  () => {
    nextTick(() => {
      if (!map) initMap();
      updateMap();
    });
  },
  { deep: true },
);
</script>

<template>
  <div class="bg-white rounded-lg shadow overflow-hidden h-full">
    <div ref="mapContainer" class="h-full"></div>
  </div>
</template>
