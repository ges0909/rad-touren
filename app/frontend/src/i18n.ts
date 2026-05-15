export type Lang = "de" | "en";

const messages = {
  subtitle: {
    de: "Plane Radtouren, Wanderungen und Roadtrips mit KI. Beschreibe einfach, was du dir vorstellst.",
    en: "Plan cycling tours, hikes, and road trips with AI. Just describe what you have in mind.",
  },
  placeholder: {
    de: "z.B. Plane einen 2-Wochen Roadtrip an der spanischen Nordküste...",
    en: "e.g. Plan a 2-week road trip along the Spanish north coast...",
  },
  btnSend: { de: "Los", en: "Go" },
  btnMarkdown: { de: "Markdown", en: "Markdown" },
  btnPdf: { de: "PDF", en: "PDF" },
  historyTitle: { de: "Letzte Anfragen", en: "Recent queries" },
  historyClear: { de: "Verlauf löschen", en: "Clear history" },
  errorNoResponse: {
    de: "Keine Antwort vom Server erhalten. Bitte prüfe das Backend-Log.",
    en: "No response from server. Please check the backend log.",
  },
  errorConnection: {
    de: "Verbindung zum Server fehlgeschlagen. Ist das Backend gestartet?",
    en: "Connection to server failed. Is the backend running?",
  },
  errorServer: {
    de: "Server-Fehler ({status}). Bitte prüfe das Backend-Log.",
    en: "Server error ({status}). Please check the backend log.",
  },
  followUpPlaceholder: {
    de: "Antwort oder Änderungswunsch eingeben...",
    en: "Type a reply or change request...",
  },
} as const;

type MessageKey = keyof typeof messages;

export function t(
  key: MessageKey,
  lang: Lang,
  params?: Record<string, string | number>,
): string {
  let text = messages[key][lang];
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      text = text.replace(`{${k}}`, String(v)) as typeof text;
    }
  }
  return text;
}
