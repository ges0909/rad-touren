<script setup lang="ts">
import { ref } from "vue";

defineProps<{ isLoading: boolean }>();
const emit = defineEmits<{ send: [message: string] }>();

const input = ref("");

function handleSubmit() {
  const message = input.value.trim();
  if (!message) return;
  emit("send", message);
  input.value = "";
}
</script>

<template>
  <form @submit.prevent="handleSubmit" class="flex gap-2">
    <input
      v-model="input"
      type="text"
      :disabled="isLoading"
      placeholder="z.B. Plane einen 2-Wochen Roadtrip an der spanischen Nordküste..."
      class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
    />
    <button
      type="submit"
      :disabled="isLoading || !input.trim()"
      class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
    >
      <span v-if="isLoading">⏳</span>
      <span v-else>Senden</span>
    </button>
  </form>
</template>
