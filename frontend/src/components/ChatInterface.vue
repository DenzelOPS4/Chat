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
    const response = await axios.post('https://chat-u7b1.onrender.com/api/chat/', { text: userMsg });
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
  <div class="landing">
    <!-- small icon top-left -->
    <div class="appIcon" aria-hidden="true">
      <span class="dot"></span>
    </div>

    <!-- center hero -->
    <div class="hero">
      <h2 class="heroHello">Hi there!</h2>
      <h1 class="heroTitle">What would you like to know?</h1>
      <p class="heroSub">
        Use one of the most common prompts below<br />
        or ask your own question
      </p>
    </div>

    <!-- messages (optional): show only after first message -->
    <main v-if="messages.length" ref="messagesContainer" class="messages">
      <div class="messagesInner">
        <div
          v-for="msg in messages"
          :key="msg.id"
          :class="['msgRow', msg.sender === 'user' ? 'right' : 'left']"
        >
          <div :class="['msgBubble', msg.sender === 'user' ? 'user' : 'bot', msg.isError ? 'err' : '']">
            <div class="msgText">{{ msg.text }}</div>
            <div class="msgMeta">
              <span>{{ msg.timestamp }}</span>
              <span v-if="msg.sender === 'user'" class="ticks">✓✓</span>
            </div>
          </div>
        </div>

        <div v-if="isLoading" class="msgRow left">
          <div class="msgBubble bot">
            <span class="typingDot" style="animation-delay:0s"></span>
            <span class="typingDot" style="animation-delay:.15s"></span>
            <span class="typingDot" style="animation-delay:.3s"></span>
          </div>
        </div>
      </div>
    </main>

    <!-- bottom composer -->
    <footer class="composer">
      <div class="composerBar">
        <button
          type="button"
          class="micBtn"
          :class="{ rec: isRecording }"
          @click="toggleRecording"
          title="Голосовой ввод"
          aria-label="Голосовой ввод"
        >
          🎙️
        </button>

        <input
          v-model="inputText"
          @keyup.enter="sendMessage"
          class="composerInput"
          type="text"
          placeholder="Ask whatever you want"
        />

        <button
          type="button"
          class="sendBtn"
          @click="sendMessage"
          :disabled="!canSend"
          aria-label="Отправить"
          title="Отправить"
        >
          ➤
        </button>
      </div>
    </footer>
  </div>
</template>

<style scoped>
/* full-screen dark blue background */
.landing {
  min-height: 100vh;
  width: 100%;
  background: #0b2a57;
  position: relative;
  overflow: hidden;
  font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial, "Noto Sans", "Apple Color Emoji",
    "Segoe UI Emoji";
}

/* top-left rounded square icon */
.appIcon {
  position: absolute;
  top: 22px;
  left: 22px;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.10);
  display: grid;
  place-items: center;
}
.appIcon .dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.80);
}

/* centered hero text */
.hero {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  text-align: center;
  padding: 24px;
  pointer-events: none;
}
.heroHello {
  margin: 0;
  color: rgba(255, 255, 255, 0.92);
  font-weight: 600;
  font-size: 28px;
  line-height: 1.15;
}
.heroTitle {
  margin: 10px 0 0;
  color: rgba(255, 255, 255, 0.92);
  font-weight: 700;
  font-size: 34px;
  line-height: 1.15;
}
.heroSub {
  margin: 12px 0 0;
  color: rgba(255, 255, 255, 0.62);
  font-size: 14px;
  line-height: 1.5;
}

/* messages area (appears after first message) */
.messages {
  position: absolute;
  top: 92px;
  left: 0;
  right: 0;
  bottom: 110px;
  overflow: auto;
  padding: 0 18px;
}
.messagesInner {
  max-width: 860px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.msgRow {
  display: flex;
}
.msgRow.left { justify-content: flex-start; }
.msgRow.right { justify-content: flex-end; }

.msgBubble {
  max-width: min(78ch, 92%);
  border-radius: 18px;
  padding: 12px 14px;
  border: 1px solid rgba(255, 255, 255, 0.10);
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(10px);
}
.msgBubble.user {
  background: rgba(255, 255, 255, 0.10);
}
.msgBubble.err {
  background: rgba(255, 80, 120, 0.12);
  border-color: rgba(255, 80, 120, 0.22);
  color: rgba(255, 210, 220, 0.98);
}
.msgText {
  white-space: pre-wrap;
  word-break: break-word;
  overflow-wrap: anywhere;
  line-height: 1.45;
}
.msgMeta {
  margin-top: 8px;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  font-size: 11px;
  opacity: 0.75;
  user-select: none;
}
.ticks { font-weight: 700; }

/* typing dots */
.typingDot {
  width: 7px;
  height: 7px;
  border-radius: 999px;
  display: inline-block;
  margin-right: 6px;
  background: rgba(255, 255, 255, 0.75);
  animation: bounce 0.9s infinite ease-in-out;
}
@keyframes bounce {
  0%, 80%, 100% { transform: translateY(0); opacity: 0.6; }
  40% { transform: translateY(-4px); opacity: 1; }
}

/* bottom input bar */
.composer {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 26px;
  padding: 0 18px;
}
.composerBar {
  max-width: 860px;
  margin: 0 auto;
  height: 54px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.18);
  border: 1px solid rgba(255, 255, 255, 0.10);
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  backdrop-filter: blur(10px);
}

.micBtn, .sendBtn {
  width: 42px;
  height: 42px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.10);
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.90);
  display: grid;
  place-items: center;
  font-size: 20px;
  cursor: pointer;
  user-select: none;
}
.micBtn.rec {
  background: rgba(255, 80, 120, 0.70);
  border-color: rgba(255, 80, 120, 0.35);
}
.sendBtn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.composerInput {
  flex: 1;
  height: 42px;
  border: 0;
  outline: none;
  background: transparent;
  color: rgba(255, 255, 255, 0.92);
  font-size: 16px;
}
.composerInput::placeholder {
  color: rgba(255, 255, 255, 0.55);
}
</style>
