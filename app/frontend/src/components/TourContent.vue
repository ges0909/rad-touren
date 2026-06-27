<script setup lang="ts">
import { computed } from "vue";
import { marked } from "marked";
import DOMPurify from "dompurify";

const props = defineProps<{ markdown: string; gpx: string }>();

const renderedHtml = computed(() => {
  let md = props.markdown;
  // Strip YAML front matter if present (---\n...\n---)
  if (md.startsWith("---")) {
    const end = md.indexOf("---", 3);
    if (end !== -1) {
      md = md.slice(end + 3).trim();
    }
  }
  const raw = marked(md) as string;
  return DOMPurify.sanitize(raw);
});

const filename = computed(() => {
  // Extract first heading as filename basis
  const match = props.markdown.match(/^#{1,3}\s+(.+)$/m);
  if (!match) return "tour";
  return match[1]
    .trim()
    .toLowerCase()
    .replace(/[äÄ]/g, "ae")
    .replace(/[öÖ]/g, "oe")
    .replace(/[üÜ]/g, "ue")
    .replace(/ß/g, "ss")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 60);
});
</script>

<template>
  <div class="bg-white rounded-lg shadow p-6 overflow-y-auto h-full">
    <div class="prose prose-sm max-w-none" v-html="renderedHtml"></div>

    <!-- Download buttons -->
    <div class="mt-6 pt-4 border-t flex gap-3">
      <a
        :href="
          'data:text/markdown;charset=utf-8,' + encodeURIComponent(markdown)
        "
        :download="filename + '.md'"
        class="inline-flex items-center justify-center px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded-md transition"
      >
        📄 Markdown
      </a>
      <a
        v-if="gpx"
        :href="
          'data:application/gpx+xml;charset=utf-8,' + encodeURIComponent(gpx)
        "
        :download="filename + '.gpx'"
        class="inline-flex items-center justify-center px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded-md transition"
      >
        🗺️ GPX
      </a>
    </div>
  </div>
</template>
