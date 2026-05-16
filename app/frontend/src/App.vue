<script setup lang="ts">
import { ref, computed } from "vue";
import ChatInput from "./components/ChatInput.vue";
import TourContent from "./components/TourContent.vue";
import TourMap from "./components/TourMap.vue";
import { t, type Lang } from "./i18n";

const tourMarkdown = ref("");
const isLoading = ref(false);
const errorMessage = ref("");
const statusMessages = ref<string[]>([]);
const language = ref<Lang>("de");
const chatInputRef = ref<InstanceType<typeof ChatInput> | null>(null);
const mapData = ref<{
  waypoints: [number, number][];
  routes: [number, number][][];
  pois: { lat: number; lon: number; name: string; category?: string }[];
  elevation: [number, number][];
}>({
  waypoints: [],
  routes: [],
  pois: [],
  elevation: [],
});
const splitPercent = ref(50);

const hasMapData = computed(
  () =>
    mapData.value.waypoints.length > 0 ||
    mapData.value.routes.length > 0 ||
    mapData.value.pois.length > 0,
);

function startResize(e: MouseEvent) {
  e.preventDefault();
  e.stopPropagation();
  const container = (e.target as HTMLElement).closest(
    "[data-split-container]",
  ) as HTMLElement;
  if (!container) return;
  const startX = e.clientX;
  const startPercent = splitPercent.value;
  const containerWidth = container.offsetWidth;

  // Prevent text selection and pointer events on children during drag
  document.body.style.userSelect = "none";
  document.body.style.cursor = "col-resize";

  function onMove(ev: MouseEvent) {
    ev.preventDefault();
    const delta = ev.clientX - startX;
    const newPercent = startPercent + (delta / containerWidth) * 100;
    splitPercent.value = Math.max(20, Math.min(80, newPercent));
  }

  function onUp() {
    document.body.style.userSelect = "";
    document.body.style.cursor = "";
    document.removeEventListener("mousemove", onMove);
    document.removeEventListener("mouseup", onUp);
  }

  document.addEventListener("mousemove", onMove);
  document.addEventListener("mouseup", onUp);
}

async function handleSend(message: string) {
  isLoading.value = true;
  tourMarkdown.value = "";
  errorMessage.value = "";
  statusMessages.value = [];
  mapData.value = { waypoints: [], routes: [], pois: [], elevation: [] };

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        language: language.value,
        session_id: "default",
      }),
    });

    if (!response.ok) {
      errorMessage.value = t("errorServer", language.value, {
        status: response.status,
      });
      return;
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) return;

    let buffer = "";
    let receivedData = false;
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      let currentEvent = "";
      for (const line of lines) {
        if (line.startsWith("event:")) {
          currentEvent = line.slice(6).trim();
        } else if (line.startsWith("data:")) {
          const data = line.slice(5).trim();
          if (!data) continue;
          try {
            const parsed = JSON.parse(data);
            receivedData = true;
            if (currentEvent === "error" || parsed.error) {
              errorMessage.value = parsed.error;
            } else if (currentEvent === "tour" || parsed.markdown) {
              tourMarkdown.value = parsed.markdown;
            } else if (currentEvent === "map") {
              if (parsed.waypoints) {
                mapData.value.waypoints.push(...parsed.waypoints);
              }
              if (parsed.route) {
                mapData.value.routes.push(parsed.route);
              }
              if (parsed.pois) {
                mapData.value.pois.push(...parsed.pois);
              }
            } else if (currentEvent === "elevation" && parsed.profile) {
              mapData.value.elevation = parsed.profile;
            } else if (currentEvent === "status" && parsed.message) {
              if (!statusMessages.value.includes(parsed.message)) {
                statusMessages.value.push(parsed.message);
              }
            }
          } catch {
            // ignore parse errors
          }
          currentEvent = "";
        }
      }
    }

    if (!receivedData && !errorMessage.value) {
      errorMessage.value = t("errorNoResponse", language.value);
    }
  } catch (error) {
    errorMessage.value = t("errorConnection", language.value);
  } finally {
    isLoading.value = false;
    chatInputRef.value?.clear();
  }
}
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 py-6">
    <!-- Header -->
    <header class="mb-6 flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">Gerrit on Tour</h1>
        <p class="text-gray-600 mt-1">
          {{ t("subtitle", language) }}
        </p>
      </div>
      <div class="flex items-center gap-1 bg-gray-100 rounded-md p-0.5">
        <button
          :class="[
            'px-2 py-1 text-sm rounded transition',
            language === 'de'
              ? 'bg-white shadow text-gray-900'
              : 'text-gray-500 hover:text-gray-700',
          ]"
          @click="language = 'de'"
        >
          DE
        </button>
        <button
          :class="[
            'px-2 py-1 text-sm rounded transition',
            language === 'en'
              ? 'bg-white shadow text-gray-900'
              : 'text-gray-500 hover:text-gray-700',
          ]"
          @click="language = 'en'"
        >
          EN
        </button>
      </div>
    </header>

    <!-- Chat Input -->
    <ChatInput
      ref="chatInputRef"
      :is-loading="isLoading"
      :language="language"
      @send="handleSend"
    />

    <!-- Status Feed (live tool calls) -->
    <div
      v-if="isLoading && statusMessages.length > 0"
      class="mt-3 px-4 py-2 bg-blue-50 border border-blue-100 rounded-lg"
    >
      <p
        v-for="(msg, i) in statusMessages"
        :key="i"
        class="text-xs text-blue-700 font-mono truncate"
      >
        {{ msg }}
      </p>
    </div>

    <!-- Error Display -->
    <div
      v-if="errorMessage"
      class="mt-4 px-4 py-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3"
    >
      <span class="text-red-500 text-lg leading-none">⚠️</span>
      <div class="flex-1">
        <p class="text-sm text-red-800">{{ errorMessage }}</p>
      </div>
      <button
        @click="errorMessage = ''"
        class="text-red-400 hover:text-red-600 text-lg leading-none"
      >
        ✕
      </button>
    </div>

    <!-- Tour Result + Map -->
    <div
      v-if="tourMarkdown || hasMapData"
      data-split-container
      class="mt-6 flex flex-col lg:flex-row"
      style="height: 80vh"
    >
      <div
        v-if="tourMarkdown"
        :style="{ width: splitPercent + '%' }"
        class="overflow-hidden min-w-0"
      >
        <TourContent :markdown="tourMarkdown" />
      </div>
      <div
        v-if="tourMarkdown && hasMapData"
        class="hidden lg:flex items-center justify-center w-3 cursor-col-resize bg-gray-100 hover:bg-blue-200 active:bg-blue-300 transition-colors shrink-0 select-none"
        @mousedown="startResize"
      >
        <div class="w-0.5 h-8 bg-gray-400 rounded"></div>
      </div>
      <div
        :style="{ width: tourMarkdown ? 100 - splitPercent + '%' : '100%' }"
        class="overflow-hidden min-w-0"
      >
        <TourMap
          :waypoints="mapData.waypoints"
          :routes="mapData.routes"
          :pois="mapData.pois"
          :elevation="mapData.elevation"
        />
      </div>
    </div>
  </div>
</template>
