<template>
  <div class="plan-page">
    <div class="plan-card">
      <h1 class="plan-title">Ваш план</h1>
      <p class="plan-placeholder">Здесь будет отображаться ваш персональный план обучения</p>
    </div>
  </div>
</template>

<style scoped>
.plan-page {
  min-height: 80vh;
  background-color: #f5f5f5;
  padding: 40px 20px;
  display: flex;
  justify-content: center;
  align-items: flex-start;
}

.plan-card {
  max-width: 800px;
  width: 100%;
  background: white;
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.plan-title {
  font-size: 28px;
  font-weight: 600;
  color: #7a4e30;
  margin-bottom: 20px;
  -webkit-text-stroke: 0.5px #7a4e30;
}

.plan-placeholder {
  font-size: 16px;
  color: #666;
  line-height: 1.5;
}
</style>