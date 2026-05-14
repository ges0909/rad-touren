<script setup lang="ts">
import { computed } from "vue";
import { marked } from "marked";

const props = defineProps<{ markdown: string }>();

const renderedHtml = computed(() => {
  return marked(props.markdown) as string;
});
</script>

<template>
  <div class="bg-white rounded-lg shadow p-6 overflow-y-auto max-h-[80vh]">
    <div class="prose prose-sm max-w-none" v-html="renderedHtml"></div>

    <!-- Download buttons -->
    <div class="mt-6 pt-4 border-t flex gap-3">
      <a
        :href="
          'data:text/markdown;charset=utf-8,' + encodeURIComponent(markdown)
        "
        download="tour.md"
        class="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded-md transition"
      >
        📄 Markdown
      </a>
      <button
        class="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded-md transition"
        @click="window.print()"
      >
        📑 PDF
      </button>
    </div>
  </div>
</template>
