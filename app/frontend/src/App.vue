<script setup lang="ts">
import { ref } from "vue";
import ChatInput from "./components/ChatInput.vue";
import TourContent from "./components/TourContent.vue";
import TourMap from "./components/TourMap.vue";

const messages = ref<Array<{ role: string; content: string }>>([]);
const tourMarkdown = ref("");
const isLoading = ref(false);
const tourType = ref("road");

async function handleSend(message: string) {
  messages.value.push({ role: "user", content: message });
  isLoading.value = true;
  tourMarkdown.value = "";

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        tour_type: tourType.value,
        session_id: "default",
      }),
    });

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) return;

    let buffer = "";
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
            // Handle based on preceding event line
            if (parsed.markdown) {
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
  } catch (error) {
    messages.value.push({
      role: "assistant",
      content: "Fehler bei der Verbindung zum Server.",
    });
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

    <!-- Tour Type Selector -->
    <div class="mb-4 flex gap-2">
      <button
        v-for="t in [
          { id: 'road', label: '🚗 Roadtrip' },
          { id: 'bike', label: '🚲 Radtour' },
          { id: 'hike', label: '🥾 Wanderung' },
        ]"
        :key="t.id"
        :class="[
          'px-3 py-1.5 rounded-md text-sm font-medium transition',
          tourType === t.id
            ? 'bg-blue-600 text-white'
            : 'bg-gray-200 text-gray-700 hover:bg-gray-300',
        ]"
        @click="tourType = t.id"
      >
        {{ t.label }}
      </button>
    </div>

    <!-- Chat Input -->
    <ChatInput :is-loading="isLoading" @send="handleSend" />

    <!-- Messages -->
    <div v-if="messages.length" class="mt-4 space-y-2">
      <div
        v-for="(msg, i) in messages"
        :key="i"
        :class="[
          'px-3 py-2 rounded-lg text-sm max-w-[80%]',
          msg.role === 'user'
            ? 'bg-blue-100 text-blue-900 ml-auto'
            : 'bg-gray-100 text-gray-800',
        ]"
      >
        {{ msg.content }}
      </div>
    </div>

    <!-- Tour Result -->
    <div v-if="tourMarkdown" class="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
      <TourContent :markdown="tourMarkdown" />
      <TourMap />
    </div>
  </div>
</template>
