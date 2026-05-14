<script setup lang="ts">
import { ref, computed } from "vue";

defineProps<{ isLoading: boolean }>();
const emit = defineEmits<{ send: [message: string] }>();

const input = ref("");
const history = ref<string[]>(loadHistory());
const showHistory = ref(false);

function loadHistory(): string[] {
  try {
    return JSON.parse(localStorage.getItem("chat-history") || "[]");
  } catch {
    return [];
  }
}

function saveHistory() {
  localStorage.setItem("chat-history", JSON.stringify(history.value));
}

function handleSubmit() {
  const message = input.value.trim();
  if (!message) return;
  emit("send", message);

  // Add to history (deduplicate, keep last 20)
  history.value = [
    message,
    ...history.value.filter((h) => h !== message),
  ].slice(0, 20);
  saveHistory();

  input.value = "";
  showHistory.value = false;
}

function selectFromHistory(entry: string) {
  input.value = entry;
  showHistory.value = false;
}

const hasHistory = computed(() => history.value.length > 0);
</script>

<template>
  <div class="relative">
    <form @submit.prevent="handleSubmit">
      <div class="relative">
        <textarea
          v-model="input"
          :disabled="isLoading"
          placeholder="z.B. Plane einen 2-Wochen Roadtrip an der spanischen Nordküste..."
          rows="3"
          class="w-full px-4 py-3 pr-20 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 resize-none text-base"
          @keydown.enter.exact.prevent="handleSubmit"
        />
        <button
          v-if="hasHistory"
          type="button"
          @click="showHistory = !showHistory"
          class="absolute right-3 top-3 text-gray-400 hover:text-gray-600 transition"
          title="Letzte Anfragen"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-5 w-5"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              fill-rule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z"
              clip-rule="evenodd"
            />
          </svg>
        </button>
        <button
          type="submit"
          :disabled="isLoading || !input.trim()"
          class="absolute right-3 bottom-3 px-3 py-1.5 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
        >
          <span v-if="isLoading">⏳</span>
          <span v-else>Los</span>
        </button>
      </div>
    </form>

    <!-- History Dropdown -->
    <div
      v-if="showHistory && hasHistory"
      class="absolute z-10 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-y-auto"
    >
      <button
        v-for="(entry, i) in history"
        :key="i"
        type="button"
        @click="selectFromHistory(entry)"
        class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 border-b border-gray-50 last:border-b-0 truncate"
      >
        {{ entry }}
      </button>
    </div>
  </div>
</template>
