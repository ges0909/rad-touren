<script setup lang="ts">
import { ref } from "vue";
import ChatInput from "./components/ChatInput.vue";
import TourContent from "./components/TourContent.vue";
import TourMap from "./components/TourMap.vue";
import { t, type Lang } from "./i18n";

const messages = ref<Array<{ role: string; content: string }>>([]);
const tourMarkdown = ref("");
const isLoading = ref(false);
const errorMessage = ref("");
const language = ref<Lang>("de");
const mapData = ref<{
  waypoints: [number, number][];
  route: [number, number][];
}>({
  waypoints: [],
  route: [],
});
const splitPercent = ref(50);

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

function handleReset() {
  tourMarkdown.value = "";
  errorMessage.value = "";
  mapData.value = { waypoints: [], route: [] };
}

async function handleSend(message: string) {
  messages.value.push({ role: "user", content: message });
  isLoading.value = true;
  tourMarkdown.value = "";
  errorMessage.value = "";
  mapData.value = { waypoints: [], route: [] };

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

      for (const line of lines) {
        if (line.startsWith("data:")) {
          const data = line.slice(5).trim();
          if (!data) continue;
          try {
            const parsed = JSON.parse(data);
            receivedData = true;
            if (parsed.error) {
              errorMessage.value = parsed.error;
            } else if (parsed.markdown) {
              tourMarkdown.value = parsed.markdown;
            } else if (parsed.waypoints) {
              mapData.value.waypoints.push(...parsed.waypoints);
            } else if (parsed.route) {
              mapData.value.route = parsed.route;
            } else if (parsed.message) {
              messages.value.push({
                role: "assistant",
                content: parsed.message,
              });
            }
          } catch {
            // ignore parse errors
          }
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
  }
}
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 py-6">
    <!-- Header -->
    <header class="mb-6 flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">Trip Planner</h1>
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
      :is-loading="isLoading"
      :has-result="!!tourMarkdown"
      :language="language"
      @send="handleSend"
      @reset="handleReset"
    />

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

    <!-- Tour Result -->
    <div
      v-if="tourMarkdown"
      data-split-container
      class="mt-6 flex flex-col lg:flex-row"
      style="height: 80vh"
    >
      <div
        :style="{ width: splitPercent + '%' }"
        class="overflow-hidden min-w-0"
      >
        <TourContent :markdown="tourMarkdown" />
      </div>
      <div
        class="hidden lg:flex items-center justify-center w-3 cursor-col-resize bg-gray-100 hover:bg-blue-200 active:bg-blue-300 transition-colors shrink-0 select-none"
        @mousedown="startResize"
      >
        <div class="w-0.5 h-8 bg-gray-400 rounded"></div>
      </div>
      <div
        :style="{ width: 100 - splitPercent + '%' }"
        class="overflow-hidden min-w-0"
      >
        <TourMap :waypoints="mapData.waypoints" :route="mapData.route" />
      </div>
    </div>
  </div>
</template>
