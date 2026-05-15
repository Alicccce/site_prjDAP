<template>
  <header class="app-header">
    <div class="header-inner">
      <router-link to="/start" class="logo">Dapdep</router-link>

      <nav v-if="isAuthenticated" class="header-nav">
        <router-link to="/start" class="nav-link">Главная</router-link>
        <router-link to="/search" class="nav-link">Поиск</router-link>
        <router-link to="/profile" class="nav-link">Профиль</router-link>
        <button @click="handleLogout" class="logout-btn">Выйти</button>
      </nav>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()

const isAuthenticated = computed(() => !!userStore.token)

const handleLogout = () => {
  userStore.clearUser()
  router.push('/login')
}
</script>

<style scoped>
.app-header {
  background-color: #f5f5f5;
  border-bottom: 2px solid #e0e0e0;
  padding: 0 40px;
  height: 70px;
  display: flex;
  align-items: center;
}

.header-inner {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo {
  font-size: 32px;
  font-weight: 700;
  color: #3de0cd;
  -webkit-text-stroke: 2px #7a4e30;
  text-decoration: none;
  line-height: 1;
}

.header-nav {
  display: flex;
  align-items: center;
  gap: 24px;
}

.nav-link {
  font-size: 15px;
  color: #7a4e30;
  text-decoration: none;
  font-weight: 500;
  transition: opacity 0.2s;
}

.nav-link:hover {
  opacity: 0.7;
}

.nav-link.router-link-active {
  border-bottom: 2px solid #7a4e30;
  padding-bottom: 2px;
}

.logout-btn {
  padding: 8px 18px;
  background: none;
  border: 1.5px solid #7a4e30;
  color: #7a4e30;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.logout-btn:hover {
  background-color: #7a4e30;
  color: white;
}

@media (max-width: 600px) {
  .app-header {
    padding: 0 16px;
  }
  .logo {
    font-size: 24px;
  }
  .header-nav {
    gap: 12px;
  }
  .nav-link {
    font-size: 13px;
  }
  .logout-btn {
    padding: 6px 12px;
    font-size: 13px;
  }
}
</style>
