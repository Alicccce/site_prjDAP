<template>
  <div class="dialog-overlay" @click.self="$emit('close')">
    <div class="dialog-box">
      <div class="dialog-header">
        <h2 class="dialog-title">Расскажите о своих навыках</h2>
        <button class="close-btn" @click="$emit('close')">✕</button>
      </div>
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
      </div>
      <p class="progress-label">Вопрос {{ currentStep + 1 }} из {{ questions.length }}</p>

      <div class="chat-area" ref="chatArea">
        <div v-for="(msg, idx) in messages" :key="idx" :class="['message', msg.role]">
          <div class="bubble">{{ msg.text }}</div>
        </div>
        <div v-if="typing" class="message bot">
          <div class="bubble typing-indicator"><span></span><span></span><span></span></div>
        </div>
      </div>

      <div v-if="!finished" class="input-area">
        <div v-if="currentQuestion && currentQuestion.type === 'chips'" class="chips-area">
          <button v-for="opt in currentQuestion.options" :key="opt"
            :class="['chip', { selected: selectedChips.includes(opt) }]"
            @click="toggleChip(opt)">{{ opt }}</button>
        </div>
        <div v-if="!currentQuestion || currentQuestion.type === 'text'" class="text-input-area">
          <input v-model="userInput" type="text"
            :placeholder="currentQuestion?.placeholder || 'Введите ответ...'"
            class="chat-input" @keydown.enter="sendAnswer" ref="inputRef" />
        </div>
        <button class="send-btn" @click="sendAnswer" :disabled="!canSend">
          {{ isLastQuestion ? 'Завершить' : 'Далее →' }}
        </button>
      </div>

      <div v-if="finished" class="finished-area">
        <p class="finished-text">Отлично! Я понял ваши навыки.</p>
        <p class="skills-summary">Найдено навыков: <strong>{{ collectedSkills.length }}</strong></p>
        <div class="skills-chips">
          <span v-for="skill in collectedSkills" :key="skill" class="skill-chip">{{ skill }}</span>
        </div>
        <button class="find-btn" @click="$emit('done', collectedSkills)">
          Найти подходящие должности →
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted } from 'vue'

const emit = defineEmits(['close', 'done'])

const questions = [
  { id: 'languages', type: 'chips', bot: 'Привет! Начнём с языков программирования — какие из них вы знаете?', options: ['Python', 'JavaScript', 'TypeScript', 'Java', 'C#', 'C++', 'Go', 'PHP', 'Ruby', 'Swift', 'Kotlin', 'Rust', 'Ни одного'], skillsKey: true },
  { id: 'frameworks', type: 'chips', bot: 'Хорошо! Какие фреймворки или библиотеки вы использовали?', options: ['React', 'Vue.js', 'Angular', 'Django', 'FastAPI', 'Flask', 'Spring', 'Node.js', 'Next.js', 'Laravel', 'Ни одного'], skillsKey: true },
  { id: 'databases', type: 'chips', bot: 'С какими базами данных вы работали?', options: ['PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'SQLite', 'Elasticsearch', 'ClickHouse', 'MS SQL', 'Ни одного'], skillsKey: true },
  { id: 'devops', type: 'chips', bot: 'Знакомы ли вы с инструментами DevOps или облачными сервисами?', options: ['Docker', 'Kubernetes', 'Git', 'CI/CD', 'AWS', 'Azure', 'GCP', 'Linux', 'Terraform', 'Ни одного'], skillsKey: true },
  { id: 'extra', type: 'text', bot: 'Есть ли ещё навыки?', placeholder: 'Например: Machine Learning, SQL, Figma', skillsKey: true },
  { id: 'experience', type: 'chips', bot: 'Какой у вас опыт работы?', options: ['Нет опыта', 'До 1 года', '1–3 года', '3–5 лет', '5+ лет'], skillsKey: false }
]

const messages = ref([])
const currentStep = ref(0)
const userInput = ref('')
const selectedChips = ref([])
const typing = ref(false)
const finished = ref(false)
const collectedSkills = ref([])
const chatArea = ref(null)
const inputRef = ref(null)

const currentQuestion = computed(() => questions[currentStep.value] || null)
const isLastQuestion = computed(() => currentStep.value === questions.length - 1)
const progressPercent = computed(() => Math.round((currentStep.value / questions.length) * 100))
const canSend = computed(() => {
  if (!currentQuestion.value) return false
  if (currentQuestion.value.type === 'chips') return selectedChips.value.length > 0
  return userInput.value.trim().length > 0
})

const scrollToBottom = async () => {
  await nextTick()
  if (chatArea.value) chatArea.value.scrollTop = chatArea.value.scrollHeight
}

const addBotMessage = async (text) => {
  typing.value = true
  await scrollToBottom()
  await new Promise(r => setTimeout(r, 600))
  typing.value = false
  messages.value.push({ role: 'bot', text })
  await scrollToBottom()
}

const addUserMessage = (text) => {
  messages.value.push({ role: 'user', text })
  scrollToBottom()
}

const toggleChip = (opt) => {
  const idx = selectedChips.value.indexOf(opt)
  if (idx === -1) {
    if (opt === 'Ни одного') { selectedChips.value = ['Ни одного'] }
    else { selectedChips.value = selectedChips.value.filter(c => c !== 'Ни одного'); selectedChips.value.push(opt) }
  } else { selectedChips.value.splice(idx, 1) }
}

const extractSkillsFromText = (text) => {
  return text.split(/[,;\/\n]|(?:\s+и\s+)|(?:\s+или\s+)/i)
    .map(p => p.trim())
    .filter(p => p.length > 1 && p.toLowerCase() !== 'нет' && p.toLowerCase() !== 'ничего')
}

const sendAnswer = async () => {
  if (!canSend.value) return
  const q = currentQuestion.value
  let answerText = '', skillsToAdd = []
  if (q.type === 'chips') {
    const chosen = selectedChips.value.filter(c => c !== 'Ни одного')
    answerText = chosen.length > 0 ? chosen.join(', ') : 'Ни одного'
    if (q.skillsKey) skillsToAdd = chosen
  } else {
    answerText = userInput.value.trim()
    if (q.skillsKey) skillsToAdd = extractSkillsFromText(answerText)
  }
  for (const skill of skillsToAdd) {
    if (!collectedSkills.value.includes(skill)) collectedSkills.value.push(skill)
  }
  addUserMessage(answerText)
  userInput.value = ''; selectedChips.value = []
  if (currentStep.value < questions.length - 1) {
    currentStep.value++
    await addBotMessage(questions[currentStep.value].bot)
    await nextTick()
    if (inputRef.value) inputRef.value.focus()
  } else {
    await addBotMessage('Спасибо! Теперь я подберу для вас подходящие должности.')
    finished.value = true
  }
}

onMounted(async () => {
  await addBotMessage(questions[0].bot)
  await nextTick()
  if (inputRef.value) inputRef.value.focus()
})
</script>

<style scoped>
.dialog-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.55); display: flex; align-items: center; justify-content: center; z-index: 1000; padding: 20px; }
.dialog-box { background: white; border-radius: 16px; width: 100%; max-width: 600px; max-height: 90vh; display: flex; flex-direction: column; box-shadow: 0 20px 60px rgba(0,0,0,0.3); overflow: hidden; }
.dialog-header { display: flex; align-items: center; justify-content: space-between; padding: 20px 24px 12px; border-bottom: 1px solid #f0f0f0; }
.dialog-title { font-size: 18px; font-weight: 600; color: #7a4e30; margin: 0; }
.close-btn { background: none; border: none; font-size: 18px; color: #999; cursor: pointer; padding: 4px 8px; border-radius: 4px; width: auto; margin: 0; }
.close-btn:hover { background: #f5f5f5; color: #333; }
.progress-bar { height: 4px; background: #f0f0f0; margin: 0 24px; }
.progress-fill { height: 100%; background: linear-gradient(90deg, #3de0cd, #7a4e30); border-radius: 2px; transition: width 0.4s ease; }
.progress-label { font-size: 12px; color: #999; text-align: right; padding: 4px 24px 0; margin: 0; }
.chat-area { flex: 1; overflow-y: auto; padding: 16px 24px; display: flex; flex-direction: column; gap: 12px; min-height: 200px; max-height: 320px; }
.message { display: flex; }
.message.bot { justify-content: flex-start; }
.message.user { justify-content: flex-end; }
.bubble { max-width: 80%; padding: 10px 14px; border-radius: 12px; font-size: 14px; line-height: 1.5; }
.message.bot .bubble { background: #f0f0f0; color: #333; border-bottom-left-radius: 4px; }
.message.user .bubble { background: #7a4e30; color: white; border-bottom-right-radius: 4px; }
.typing-indicator { display: flex; gap: 4px; align-items: center; padding: 12px 16px; }
.typing-indicator span { width: 7px; height: 7px; background: #999; border-radius: 50%; animation: bounce 1.2s infinite; }
.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce { 0%, 60%, 100% { transform: translateY(0); } 30% { transform: translateY(-6px); } }
.input-area { padding: 12px 24px 20px; border-top: 1px solid #f0f0f0; display: flex; flex-direction: column; gap: 10px; }
.chips-area { display: flex; flex-wrap: wrap; gap: 8px; }
.chip { padding: 6px 14px; border: 1.5px solid #ddd; border-radius: 20px; background: white; color: #333; font-size: 13px; cursor: pointer; transition: all 0.2s; width: auto; margin: 0; }
.chip:hover { border-color: #7a4e30; color: #7a4e30; background: #c0950813; }
.chip.selected { background: #7a4e30; color: white; border-color: #7a4e30; }
.text-input-area { display: flex; }
.chat-input { flex: 1; padding: 10px 14px; border: 1.5px solid #ddd; border-radius: 8px; font-size: 14px; outline: none; }
.chat-input:focus { border-color: #7a4e30; }
.send-btn { align-self: flex-end; padding: 10px 24px; background: #3de0cd; color: white; border: none; border-radius: 8px; font-size: 14px; font-weight: 500; cursor: pointer; width: auto; margin: 0; }
.send-btn:hover:not(:disabled) { background: #2abbaa; }
.send-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.finished-area { padding: 16px 24px 24px; border-top: 1px solid #f0f0f0; text-align: center; }
.finished-text { font-size: 16px; color: #333; margin-bottom: 8px; }
.skills-summary { font-size: 14px; color: #666; margin-bottom: 12px; }
.skills-chips { display: flex; flex-wrap: wrap; gap: 6px; justify-content: center; margin-bottom: 16px; }
.skill-chip { background: #3de0cd22; color: #2abbaa; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 500; }
.find-btn { padding: 12px 32px; background: #7a4e30; color: white; border: none; border-radius: 8px; font-size: 15px; font-weight: 500; cursor: pointer; width: auto; margin: 0; }
.find-btn:hover { background: #5a3b25; }
</style>
