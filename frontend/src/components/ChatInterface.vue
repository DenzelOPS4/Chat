<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue';
import axios from 'axios';

type Sender = 'user' | 'bot';

interface Message {
  id: string;
  text: string;
  sender: Sender;
  isError?: boolean;
  timestamp: string;
}

const messages = ref<Message[]>([]);
const inputText = ref('');
const isLoading = ref(false);
const isRecording = ref(false);
const messagesContainer = ref<HTMLElement | null>(null);
let recognition: any = null;

const canSend = computed(() => !isLoading.value && inputText.value.trim().length > 0);

function nowTime(): string {
  const now = new Date();
  return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function addMessage(sender: Sender, text: string, opts?: { isError?: boolean }) {
  messages.value.push({
    id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    sender,
    text,
    isError: opts?.isError,
    timestamp: nowTime(),
  });
}

async function scrollToBottom() {
  await nextTick();
  const el = messagesContainer.value;
  if (!el) return;
  el.scrollTop = el.scrollHeight;
}

watch(
  () => messages.value.length,
  () => scrollToBottom(),
);

onMounted(() => {
  const SpeechRecognition =
    (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
  if (!SpeechRecognition) return;

  recognition = new SpeechRecognition();
  recognition.lang = 'ru-RU';
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.onresult = (event: any) => {
    const transcript = event.results?.[0]?.[0]?.transcript ?? '';
    if (transcript) inputText.value = transcript;
    isRecording.value = false;
  };

  recognition.onerror = () => {
    isRecording.value = false;
  };

  recognition.onend = () => {
    isRecording.value = false;
  };
});

function toggleRecording() {
  if (!recognition) {
    alert('Голосовой ввод не поддерживается в этом браузере.');
    return;
  }
  if (isRecording.value) {
    recognition.stop();
    isRecording.value = false;
    return;
  }
  try {
    recognition.start();
    isRecording.value = true;
  } catch {
    isRecording.value = false;
  }
}

async function sendMessage() {
  if (!canSend.value) return;

  const userMsg = inputText.value.trim();
  inputText.value = '';
  addMessage('user', userMsg);
  isLoading.value = true;

  try {
    // If frontend and backend are on different domains (e.g. Render),
    // set VITE_API_BASE_URL in frontend environment:
    // VITE_API_BASE_URL=https://your-backend.onrender.com
    const apiBase = (import.meta as any).env?.VITE_API_BASE_URL?.trim() || window.location.origin;
    const apiUrl = new URL('/api/chat/', apiBase).toString();
    const response = await axios.post(apiUrl, { text: userMsg });
    const botResponse = response?.data?.response ?? '';
    addMessage('bot', botResponse || 'Пустой ответ от сервера.', { isError: !botResponse });
  } catch (error: any) {
    const errMsg =
      error?.response?.data?.error ||
      error?.message ||
      'Ошибка сети или сервера';
    addMessage('bot', errMsg, { isError: true });
  } finally {
    isLoading.value = false;
  }
}
</script>

<template>
  <!-- Page background -->
  <div class="min-h-screen w-full bg-gradient-to-br from-slate-100 to-slate-200 flex items-center justify-center p-4">
    <!-- Chat window -->
    <section
      class="w-full max-w-3xl h-[86vh] max-h-[860px] rounded-3xl overflow-hidden shadow-2xl border border-slate-200 bg-white/70 backdrop-blur-xl flex flex-col"
      aria-label="Чат"
    >
      <!-- Header -->
      <header class="shrink-0 bg-gradient-to-r from-emerald-700 to-teal-700 text-white px-5 py-4 flex items-center gap-4">
        <div class="min-w-0 flex-1">
          <div class="flex items-center gap-2">
            <h1 class="font-semibold text-xl leading-tight truncate">Чат-Бот</h1>
            <span class="inline-flex items-center gap-1 text-xs opacity-90 shrink-0">
              <span class="w-2 h-2 rounded-full bg-emerald-200"></span>
              <span v-if="isLoading">печатает…</span>
            </span>
          </div>
          <p class="text-sm opacity-90 truncate">Чат с голосовым вводом</p>
        </div>
      </header>

      <!-- Messages -->
      <main
        ref="messagesContainer"
        class="chatScroll chatBg flex-1 overflow-y-auto px-4 py-5 md:px-6 md:py-6"
      >
        <div class="mx-auto w-full max-w-2xl space-y-4">
          <div v-if="messages.length === 0" class="pt-6 flex justify-center">
            <div class="max-w-lg text-center bg-white/85 border border-slate-200 rounded-2xl px-5 py-4 shadow-sm backdrop-blur">
              <div class="text-2xl mb-2">👋</div>
              <div class="text-slate-800 font-medium">Привет! Я AI-ассистент.</div>
              <div class="text-slate-600 text-sm mt-1">
                Напишите сообщение или нажмите на кнопку микрофона.
              </div>
            </div>
          </div>

          <div v-for="msg in messages" :key="msg.id" :class="['flex', msg.sender === 'user' ? 'justify-end' : 'justify-start']">
            <div
              :class="[
                'bubble msgPop max-w-[90%] sm:max-w-[78%] rounded-2xl px-4 py-3 border',
                msg.sender === 'user'
                  ? 'bubbleUser bg-emerald-600 text-white border-emerald-700/20 rounded-br-md shadow-[0_8px_24px_rgba(16,185,129,0.20)]'
                  : 'bubbleBot bg-white text-slate-900 border-slate-200 rounded-bl-md shadow-[0_10px_28px_rgba(15,23,42,0.08)]',
                msg.isError ? 'bubbleError bg-rose-50 text-rose-800 border-rose-200 shadow-[0_10px_28px_rgba(244,63,94,0.12)]' : ''
              ]"
            >
              <div class="whitespace-pre-wrap break-words [overflow-wrap:anywhere] leading-relaxed">
                {{ msg.text }}
              </div>
              <div class="mt-2 flex items-center justify-end gap-2 text-[11px] opacity-80 select-none">
                <span>{{ msg.timestamp }}</span>
                <span v-if="msg.sender === 'user'" class="font-semibold">✓✓</span>
              </div>
            </div>
          </div>

          <!-- Loading bubble -->
          <div v-if="isLoading" class="flex justify-start">
            <div class="bubble bubbleBot bg-white border border-slate-200 rounded-2xl rounded-bl-md px-4 py-3 shadow-sm inline-flex items-center gap-2">
              <span class="w-2 h-2 rounded-full bg-slate-500 animate-bounce" style="animation-delay: 0s"></span>
              <span class="w-2 h-2 rounded-full bg-slate-500 animate-bounce" style="animation-delay: 0.15s"></span>
              <span class="w-2 h-2 rounded-full bg-slate-500 animate-bounce" style="animation-delay: 0.3s"></span>
            </div>
          </div>
        </div>
      </main>

      <!-- Composer -->
      <footer class="shrink-0 border-t border-slate-200 bg-white/80 backdrop-blur px-3 py-3">
        <div class="mx-auto w-full max-w-2xl flex items-center gap-3">
          <!-- Mic (use emoji to avoid SVG rendering issues) -->
          <button
            type="button"
            @click="toggleRecording"
            :class="[
              'btnIcon w-12 h-12 rounded-full grid place-items-center text-2xl shadow-sm border transition-colors select-none',
              isRecording ? 'bg-rose-500 border-rose-400 text-white' : 'bg-white border-slate-200 hover:bg-slate-50 text-slate-700'
            ]"
            title="Голосовой ввод"
            aria-label="Голосовой ввод"
          >
            🎙️
          </button>

          <!-- Input -->
          <div class="flex-1">
            <input
              v-model="inputText"
              @keyup.enter="sendMessage"
              type="text"
              class="composerInput w-full h-12 rounded-2xl border border-slate-200 bg-white px-4 text-[16px] text-slate-900 placeholder-slate-400 shadow-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/40 focus:border-emerald-400"
              placeholder="Сообщение…"
            />
          </div>

          <!-- Send (emoji to avoid SVG rendering issues) -->
          <button
            type="button"
            @click="sendMessage"
            :disabled="!canSend"
            class="btnPrimary w-12 h-12 rounded-full grid place-items-center text-2xl shadow-sm transition-colors select-none disabled:opacity-50 disabled:cursor-not-allowed bg-emerald-600 hover:bg-emerald-700 text-white"
            aria-label="Отправить"
            title="Отправить"
          >
            ➤
          </button>
        </div>
      </footer>
    </section>
  </div>
</template>

<style scoped>
/* Subtle WhatsApp-ish background without external images */
.chatBg {
  background:
    radial-gradient(1200px 600px at 50% -10%, rgba(16, 185, 129, 0.16), transparent 55%),
    radial-gradient(900px 500px at 110% 30%, rgba(14, 165, 233, 0.10), transparent 55%),
    radial-gradient(900px 500px at -10% 70%, rgba(99, 102, 241, 0.08), transparent 55%),
    linear-gradient(180deg, rgba(248, 250, 252, 1) 0%, rgba(241, 245, 249, 1) 100%);
}

/* Prettier scrollbars */
.chatScroll::-webkit-scrollbar {
  width: 10px;
}
.chatScroll::-webkit-scrollbar-track {
  background: transparent;
}
.chatScroll::-webkit-scrollbar-thumb {
  background: rgba(15, 23, 42, 0.18);
  border-radius: 999px;
  border: 3px solid transparent;
  background-clip: content-box;
}
.chatScroll::-webkit-scrollbar-thumb:hover {
  background: rgba(15, 23, 42, 0.28);
  border: 3px solid transparent;
  background-clip: content-box;
}

/* Bubble tails (pseudo-elements) */
.bubble {
  position: relative;
}
.bubbleUser::after {
  content: '';
  position: absolute;
  right: -6px;
  bottom: 10px;
  width: 12px;
  height: 12px;
  background: #059669; /* emerald-600 */
  transform: rotate(45deg);
  border-radius: 2px;
  opacity: 0.9;
}
.bubbleBot::after {
  content: '';
  position: absolute;
  left: -6px;
  bottom: 10px;
  width: 12px;
  height: 12px;
  background: #ffffff;
  transform: rotate(45deg);
  border-radius: 2px;
  box-shadow: -1px 1px 0 rgba(226, 232, 240, 1); /* slate-200 edge */
}
.bubbleError::after {
  /* keep tail but match error bubble */
  background: #fff1f2; /* rose-50 */
  box-shadow: -1px 1px 0 rgba(254, 205, 211, 1);
}

/* Small pop animation for messages */
@keyframes msgPopIn {
  0% { transform: translateY(6px) scale(0.98); opacity: 0; }
  100% { transform: translateY(0) scale(1); opacity: 1; }
}
.msgPop {
  animation: msgPopIn 180ms ease-out;
}

/* Buttons feel more “app-like” */
.btnIcon:active,
.btnPrimary:active {
  transform: translateY(1px);
}

.composerInput {
  transition: box-shadow 160ms ease, border-color 160ms ease;
}
.composerInput:focus {
  box-shadow: 0 0 0 6px rgba(16, 185, 129, 0.15);
}
</style>
