<script setup>
import AppHeader from './components/AppHeader.vue'
import AppFooter from './components/AppFooter.vue'
import ToastNotification from './components/ToastNotification.vue'
import Yandex from './components/Yandex.vue'
</script>

<template>
  <AppHeader />
  <main>
    <router-view />
  </main>
  <AppFooter />
  <ToastNotification />
  <Yandex />
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}
body {
  font-family: sans-serif;
}
</style>