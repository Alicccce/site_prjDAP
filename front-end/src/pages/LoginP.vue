<template>
  <div class="auth-container">
    <!-- Вход (актив. по умлч.) -->
    <div v-if="!showRegister" class="form-card">
      <h3>Вход</h3>
      <input type="email" placeholder="Email" v-model="loginEmail" />
      <p v-if="loginErrors.email" class="error">{{ loginErrors.email }}</p>
      <input type="password" placeholder="Пароль" v-model="loginPassword" />
      <p v-if="loginErrors.password" class="error">{{ loginErrors.password }}</p>
    
      <button @click="handleLogin">Войти</button>
      <p class="toggle-link" @click="showRegister = true">Зарегистрироваться</p>
    </div>

    <!-- Рег (по клику) -->
    <div v-else class="form-card">
      <h3>Регистрация</h3>
      <input type="text" placeholder="Имя" v-model="regName" />
      <p v-if="regErrors.name" class="error">{{ regErrors.name }}</p>
      <input type="email" placeholder="Email" v-model="regEmail" />
      <p v-if="regErrors.email" class="error">{{ regErrors.email }}</p>
      <input type="password" placeholder="Пароль" v-model="regPassword" />
      <p v-if="regErrors.password" class="error">{{ regErrors.password }}</p>

      <button @click="handleRegister">Зарегистрироваться</button>
      <p class="toggle-link" @click="showRegister = false">Назад ко входу</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const showRegister = ref(false)
const loginEmail = ref('')
const loginPassword = ref('')
const regName = ref('')
const regEmail = ref('')
const regPassword = ref('')
const positions = ref([])

const loginErrors = ref({})
const regErrors = ref({})

const handleLogin = () => {
  if (!validateLogin()) return
  router.push('/start')
  //console.log('Вход:', loginEmail.value)
}
const handleRegister = () => {
  if (!validateRegister()) return
  router.push('/start')
  //console.log('Регистрация:', regName.value, regEmail.value)
}

const validateEmail = (email) => {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

const validateLogin = () => {
  const errors = {}

  if (!loginEmail.value) {
    errors.email = 'Введите email'
  } else if (!validateEmail(loginEmail.value)) {
    errors.email = 'Некорректный email'
  }

  if (!loginPassword.value) {
    errors.password = 'Введите пароль'
  }

  loginErrors.value = errors
  return Object.keys(errors).length === 0
}

const validateRegister = () => {
  const errors = {}

  if (!regName.value) {
    errors.name = 'Введите имя'
  }

  if (!regEmail.value) {
    errors.email = 'Введите email'
  } else if (!validateEmail(regEmail.value)) {
    errors.email = 'Некорректный email'
  }

  if (!regPassword.value) {
    errors.password = 'Введите пароль'
  } else if (regPassword.value.length < 6) {
    errors.password = 'Минимум 6 символов'
  }

  regErrors.value = errors
  return Object.keys(errors).length === 0
}

</script>

<style scoped>
.auth-container {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  min-height: 80vh;
  background-color: #f5f5f5;
}

.form-card {
  width: 350px;
  padding: 30px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  text-align: center;
}

h3 {
  margin-bottom: 20px;
  -webkit-text-stroke: 0.7px #7a4e30;;
  color: #7a4e30;
}

input {
  display: block;
  width: 100%;
  margin: 10px 0;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  box-sizing: border-box;
  font-size: 14px;
}

button {
  width: 100%;
  padding: 12px;
  margin-top: 10px;
  background-color: #7a4e30;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 16px;
}

button:hover {
  background-color: #5a3b25;
}

.toggle-link {
  margin-top: 15px;
  color: #7a4e30;
  cursor: pointer;
  font-size: 14px;
}

.toggle-link:hover {
  text-decoration: underline;
}

.error {
  color: red;
  font-size: 12px;
  text-align: left;
}
</style>