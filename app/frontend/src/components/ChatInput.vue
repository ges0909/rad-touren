<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue";
import { t, type Lang } from "../i18n";

const props = defineProps<{
  isLoading: boolean;
  language: Lang;
}>();
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

  showHistory.value = false;
}

function clear() {
  input.value = "";
}

defineExpose({ clear });

function selectFromHistory(entry: string) {
  input.value = entry;
  showHistory.value = false;
}

function clearHistory() {
  history.value = [];
  localStorage.removeItem("chat-history");
  showHistory.value = false;
}

function handleFocusOut(e: FocusEvent) {
  // Close history if focus moves outside the component
  const target = e.relatedTarget as HTMLElement | null;
  const container = e.currentTarget as HTMLElement;
  if (!target || !container.contains(target)) {
    showHistory.value = false;
  }
}

const componentRef = ref<HTMLElement | null>(null);

function handleClickOutside(e: MouseEvent) {
  if (
    showHistory.value &&
    componentRef.value &&
    !componentRef.value.contains(e.target as Node)
  ) {
    showHistory.value = false;
  }
}

onMounted(() => document.addEventListener("click", handleClickOutside));
onUnmounted(() => document.removeEventListener("click", handleClickOutside));

const hasHistory = computed(() => history.value.length > 0);
</script>

<template>
  <div ref="componentRef" class="relative" @focusout="handleFocusOut">
    <form @submit.prevent="handleSubmit">
      <div class="relative">
        <textarea
          v-model="input"
          :disabled="isLoading"
          :placeholder="t('placeholder', props.language)"
          rows="3"
          class="w-full px-4 py-3 pr-20 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 resize-none text-base"
          @keydown.enter.exact.prevent="handleSubmit"
        />
        <button
          v-if="hasHistory"
          type="button"
          @click="showHistory = !showHistory"
          class="absolute right-3 top-3 text-gray-400 hover:text-gray-600 transition"
          :title="t('historyTitle', props.language)"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-6 w-6"
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
          <span v-else>{{ t("btnSend", props.language) }}</span>
        </button>
      </div>
    </form>

    <!-- History Dropdown -->
    <div
      v-if="showHistory && hasHistory"
      class="absolute z-10 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-y-auto list-none"
    >
      <button
        v-for="entry in history"
        :key="entry"
        type="button"
        @click="selectFromHistory(entry)"
        class="w-full text-left px-4 py-1.5 text-sm text-gray-700 hover:bg-gray-100 border-b border-gray-50 last:border-b-0 truncate"
      >
        {{ entry }}
      </button>
      <button
        type="button"
        @click="clearHistory"
        class="w-full text-left px-4 py-1.5 text-xs text-red-500 hover:bg-red-50 border-t border-gray-200"
      >
        {{ t("historyClear", props.language) }}
      </button>
    </div>
  </div>
</template>
