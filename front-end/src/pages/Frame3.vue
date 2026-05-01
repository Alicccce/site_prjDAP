<template>
  <div class="filters-page">
    <div class="filters-card">
      <h1 class="filters-title">Фильтры поиска</h1>

      <div class="filters-form">
        <!-- Специализация -->
        <div class="filter-group">
          <label class="filter-label">Специализация</label>
          <select v-model="filters.specialization" class="filter-select">
            <option value="">Любая</option>
            <option>Frontend-разработчик</option>
            <option>Backend-разработчик</option>
            <option>Data Scientist</option>
            <option>DevOps-инженер</option>
            <option>QA-инженер</option>
            <option>UX/UI-дизайнер</option>
            <option>Аналитик</option>
            <option>Продуктовый менеджер</option>
          </select>
        </div>

        <!-- Отрасль деятельности -->
        <div class="filter-group">
          <label class="filter-label">Отрасль деятельности</label>
          <select v-model="filters.industry" class="filter-select">
            <option value="">Любая</option>
            <option>Информационные технологии</option>
            <option>Финансы и банки</option>
            <option>Ритейл</option>
            <option>Маркетинг и реклама</option>
            <option>Образование</option>
            <option>Медицина</option>
            <option>Производство</option>
          </select>
        </div>

        <!-- Образование -->
        <div class="filter-group">
          <label class="filter-label">Образование</label>
          <div class="radio-group">
            <label class="radio-label">
              <input type="radio" value="" v-model="filters.education" /> Не важно
            </label>
            <label class="radio-label">
              <input type="radio" value="higher" v-model="filters.education" /> Высшее
            </label>
            <label class="radio-label">
              <input type="radio" value="incomplete_higher" v-model="filters.education" /> Неполное высшее
            </label>
            <label class="radio-label">
              <input type="radio" value="secondary" v-model="filters.education" /> Среднее специальное
            </label>
          </div>
        </div>

        <!-- Зарплата -->
        <div class="filter-group">
          <label class="filter-label">Зарплата</label>
          <div class="salary-inputs">
            <input 
              type="number" 
              v-model="filters.salaryFrom" 
              placeholder="от"
              class="salary-input"
            />
            <span class="salary-separator">—</span>
            <input 
              type="number" 
              v-model="filters.salaryTo" 
              placeholder="до"
              class="salary-input"
            />
          </div>
        </div>

        <!-- График работы -->
        <div class="filter-group">
          <label class="filter-label">График работы</label>
          <div class="checkbox-group">
            <label class="checkbox-label">
              <input type="checkbox" value="full_day" v-model="filters.schedule" /> Полный день
            </label>
            <label class="checkbox-label">
              <input type="checkbox" value="remote" v-model="filters.schedule" /> Удалённая работа
            </label>
            <label class="checkbox-label">
              <input type="checkbox" value="flexible" v-model="filters.schedule" /> Гибкий график
            </label>
          </div>
        </div>

        <!-- Кнопки -->
        <div class="filter-actions">
          <button @click="applyFilters" class="btn-primary">Применить фильтры</button>
          <button @click="resetFilters" class="btn-secondary">Сбросить все</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive } from 'vue'

const filters = reactive({
  specialization: '',
  industry: '',
  education: '',
  salaryFrom: '',
  salaryTo: '',
  schedule: []
})

const applyFilters = () => {
  console.log('Применены фильтры:', filters)
  // Здесь будет вызов API с фильтрами
}

const resetFilters = () => {
  filters.specialization = ''
  filters.industry = ''
  filters.education = ''
  filters.salaryFrom = ''
  filters.salaryTo = ''
  filters.schedule = []
}
</script>

<style scoped>
.filters-page {
  min-height: 80vh;
  background-color: #f5f5f5;
  padding: 40px 20px;
  display: flex;
  justify-content: center;
  align-items: flex-start;
}

.filters-card {
  max-width: 700px;
  width: 100%;
  background: white;
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.filters-title {
  font-size: 28px;
  font-weight: 600;
  color: #7a4e30;
  margin-bottom: 30px;
  text-align: center;
  -webkit-text-stroke: 0.5px #7a4e30;
}

.filter-group {
  margin-bottom: 25px;
}

.filter-label {
  display: block;
  font-size: 16px;
  font-weight: 500;
  color: #333;
  margin-bottom: 10px;
}

.filter-select {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  background: white;
  cursor: pointer;
}

.filter-select:focus {
  outline: none;
  border-color: #7a4e30;
}

.radio-group, .checkbox-group {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.radio-label, .checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #333;
  cursor: pointer;
}

.radio-label input, .checkbox-label input {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: #7a4e30;
}

.salary-inputs {
  display: flex;
  gap: 12px;
  align-items: center;
}

.salary-input {
  flex: 1;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
}

.salary-input:focus {
  outline: none;
  border-color: #7a4e30;
}

.salary-separator {
  color: #999;
}

.filter-actions {
  display: flex;
  gap: 15px;
  margin-top: 30px;
}

.btn-primary {
  flex: 1;
  padding: 14px;
  background-color: #3de0cd;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
  font-weight: 500;
  transition: background 0.3s;
}

.btn-primary:hover {
  background-color: #2abbaa;
}

.btn-secondary {
  flex: 1;
  padding: 14px;
  background-color: #f5f5f5;
  color: #7a4e30;
  border: 1px solid #ddd;
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
  font-weight: 500;
  transition: all 0.3s;
}

.btn-secondary:hover {
  background-color: #eee;
  border-color: #7a4e30;
}

@media (max-width: 600px) {
  .filters-card {
    padding: 20px;
  }
  
  .filters-title {
    font-size: 22px;
  }
  
  .radio-group, .checkbox-group {
    flex-direction: column;
    gap: 10px;
  }
  
  .filter-actions {
    flex-direction: column;
  }
}
</style>