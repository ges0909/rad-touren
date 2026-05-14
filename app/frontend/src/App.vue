<script setup lang="ts">
import { ref } from "vue";
import ChatInput from "./components/ChatInput.vue";
import TourContent from "./components/TourContent.vue";
import TourMap from "./components/TourMap.vue";

const messages = ref<Array<{ role: string; content: string }>>([]);
const tourMarkdown = ref("");
const isLoading = ref(false);
const errorMessage = ref("");

async function handleSend(message: string) {
  messages.value.push({ role: "user", content: message });
  isLoading.value = true;
  tourMarkdown.value = "";
  errorMessage.value = "";

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        session_id: "default",
      }),
    });

    if (!response.ok) {
      errorMessage.value = `Server-Fehler (${response.status}). Bitte prüfe das Backend-Log.`;
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
      errorMessage.value =
        "Keine Antwort vom Server erhalten. Bitte prüfe das Backend-Log.";
    }
  } catch (error) {
    errorMessage.value =
      "Verbindung zum Server fehlgeschlagen. Ist das Backend gestartet?";
  } finally {
    isLoading.value = false;
  }
}
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 py-6">
    <!-- Header -->
    <header class="mb-6">
      <h1 class="text-2xl font-bold text-gray-800">Trip Planner</h1>
      <p class="text-gray-600 mt-1">
        Plane Radtouren, Wanderungen und Roadtrips mit KI. Beschreibe einfach,
        was du dir vorstellst.
      </p>
    </header>

    <!-- Chat Input -->
    <ChatInput :is-loading="isLoading" @send="handleSend" />

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
    <div v-if="tourMarkdown" class="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
      <TourContent :markdown="tourMarkdown" />
      <TourMap />
    </div>
  </div>
</template>
