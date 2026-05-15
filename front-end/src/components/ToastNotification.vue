<template>
  <Teleport to="body">
    <div class="toast-container">
      <TransitionGroup name="toast">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          :class="['toast', `toast--${toast.type}`]"
        >
          <span class="toast-icon">{{ icons[toast.type] }}</span>
          <span class="toast-msg">{{ toast.message }}</span>
          <button class="toast-close" @click="remove(toast.id)">✕</button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup>
import { useToastStore } from '../stores/toast'
import { storeToRefs } from 'pinia'

const store = useToastStore()
const { toasts } = storeToRefs(store)
const { remove } = store

const icons = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' }
</script>

<style scoped>
.toast-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-width: 360px;
  width: calc(100vw - 40px);
}

.toast {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  border-radius: 10px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  font-size: 14px;
  font-weight: 500;
  background: white;
  border-left: 4px solid;
}

.toast--success { border-color: #3de0cd; color: #1a6b63; }
.toast--error   { border-color: #e74c3c; color: #7b1c1c; }
.toast--info    { border-color: #7a4e30; color: #4a2e1a; }
.toast--warning { border-color: #c09508; color: #6b5200; }

.toast-icon { font-size: 16px; flex-shrink: 0; }
.toast-msg  { flex: 1; line-height: 1.4; }
.toast-close {
  background: none; border: none;
  cursor: pointer; color: #aaa;
  font-size: 14px; padding: 0;
  width: auto; flex-shrink: 0;
}
.toast-close:hover { color: #333; }

.toast-enter-active { transition: all 0.3s ease; }
.toast-leave-active { transition: all 0.25s ease; }
.toast-enter-from   { opacity: 0; transform: translateX(40px); }
.toast-leave-to     { opacity: 0; transform: translateX(40px); }
</style>
