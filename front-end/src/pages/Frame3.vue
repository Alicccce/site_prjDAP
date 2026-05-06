<template>
  <div class="filters-page">
    <div class="filters-card">
      <h1 class="filters-title">Фильтры поиска</h1>
      <button @click="resetFilters" class="btn-secondary">Сбросить ответы</button>
      <p class="filters-subtitle">Укажите предпочтения — мы подберём подходящие должности</p>

      <div class="filters-form">
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
          <p v-if="validationErrors.specialization" class="error">{{ validationErrors.specialization }}</p>
        </div>

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
          <p v-if="validationErrors.industry" class="error">{{ validationErrors.industry }}</p>
        </div>

        <div class="filter-group">
          <label class="filter-label">Образование</label>
          <div class="radio-group">
            <label class="radio-label"><input type="radio" value="" v-model="filters.education" /> Не важно</label>
            <label class="radio-label"><input type="radio" value="higher" v-model="filters.education" /> Высшее</label>
            <label class="radio-label"><input type="radio" value="incomplete_higher" v-model="filters.education" /> Неполное высшее</label>
            <label class="radio-label"><input type="radio" value="secondary" v-model="filters.education" /> Среднее специальное</label>
          </div>
        </div>

        <div class="filter-group">
          <label class="filter-label">Желаемая зарплата (₽)</label>
          <div class="salary-inputs">
            <input type="number" v-model="filters.salaryFrom" placeholder="от" class="salary-input" min="0" />
            <span class="salary-separator">—</span>
            <input type="number" v-model="filters.salaryTo" placeholder="до" class="salary-input" min="0" />
          </div>
          <p v-if="validationErrors.salary" class="error">{{ validationErrors.salary }}</p>
        </div>

        <div class="filter-group">
          <label class="filter-label">График работы</label>
          <div class="checkbox-group">
            <label class="checkbox-label"><input type="checkbox" value="full_day" v-model="filters.schedule" /> Полный день</label>
            <label class="checkbox-label"><input type="checkbox" value="remote" v-model="filters.schedule" /> Удалённая работа</label>
            <label class="checkbox-label"><input type="checkbox" value="flexible" v-model="filters.schedule" /> Гибкий график</label>
            <label class="checkbox-label"><input type="checkbox" value="shift" v-model="filters.schedule" /> Сменный график</label>
          </div>
          <p v-if="validationErrors.schedule" class="error">{{ validationErrors.schedule }}</p>
        </div>

        <div class="filter-actions">
          <button @click="applyFilters" class="btn-primary">Далее - поговорим о навыках</button>
        </div>
      </div>
    </div>

    <SkillsDialog
      v-if="showDialog"
      @close="showDialog = false"
      @done="onDialogDone"
    />
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useBranch2Store } from '../stores/branch2'
import SkillsDialog from '../components/SkillsDialog.vue'

const router = useRouter()
const branch2Store = useBranch2Store()
const showDialog = ref(false)

const filters = reactive({
  specialization: '', industry: '', education: '',
  salaryFrom: '', salaryTo: '', schedule: []
})

const applyFilters = () => {
  if (!validateFilters()) return
  branch2Store.setFilters({ ...filters })
  showDialog.value = true
}

const resetFilters = () => {
  filters.specialization = ''; filters.industry = ''; filters.education = ''
  filters.salaryFrom = ''; filters.salaryTo = ''; filters.schedule = []
  validationErrors.value = {}
}

const onDialogDone = (skills) => {
  showDialog.value = false
  branch2Store.setSkills(skills)
  router.push('/suggest')
}

const validationErrors = ref({})

const validateFilters = () => {
  const errors = {}
  if (!filters.specialization) errors.specialization = 'Выберите специализацию'
  if (!filters.industry) errors.industry = 'Выберите отрасль'
  if (!filters.education) errors.education = 'Укажите образование'
  if (!filters.salaryFrom && !filters.salaryTo) errors.salary = 'Укажите желаемую зарплату'
  if (filters.schedule.length === 0) errors.schedule = 'Выберите хотя бы один график работы'
  
  validationErrors.value = errors
  return Object.keys(errors).length === 0
}

</script>

<style scoped>
.filters-page { min-height: 80vh; background-color: #f5f5f5; padding: 40px 20px; display: flex; justify-content: center; align-items: flex-start; }
.filters-card { max-width: 700px; width: 100%; background: white; border-radius: 12px; padding: 40px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.filters-title { font-size: 28px; font-weight: 600; color: #7a4e30; margin-bottom: 8px; text-align: center; }
.filters-subtitle { font-size: 14px; color: #888; text-align: center; margin-bottom: 30px; }
.filter-group { margin-bottom: 25px; }
.filter-label { display: block; font-size: 16px; font-weight: 500; color: #333; margin-bottom: 10px; }
.filter-select { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px; background: white; cursor: pointer; }
.filter-select:focus { outline: none; border-color: #7a4e30; }
.radio-group, .checkbox-group { display: flex; gap: 20px; flex-wrap: wrap; }
.radio-label, .checkbox-label { display: flex; align-items: center; gap: 8px; font-size: 14px; color: #333; cursor: pointer; }
.radio-label input, .checkbox-label input { width: 16px; height: 16px; cursor: pointer; accent-color: #3de0cd; }
.salary-inputs { display: flex; gap: 12px; align-items: center; }
.salary-input { flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px; }
.salary-input:focus { outline: none; border-color: #7a4e30; }
.salary-separator { color: #999; }
.filter-actions { display: flex; gap: 15px; margin-top: 30px; }
.btn-primary { flex: 2; padding: 14px; background-color: #7a4e30; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 15px; font-weight: 500; transition: background 0.3s; }
.btn-primary:hover { background-color: #5a3b25; }
.btn-secondary {
  background: none;
  color: #d4c53d;
  padding: 5px 12px;
  font-size: 13px;
  border-radius: 20px;
  cursor: pointer;
  margin: 0;
  border: none;
  width: auto;
  float: right;
}
.btn-secondary:hover {
  background-color: #d4ca3d;
  color: white;
}
.error {
  color: #e74c3c;
  font-size: 13px;
  margin-top: 8px;
}

@media (max-width: 600px) { .filters-card { padding: 20px; } .radio-group, .checkbox-group { flex-direction: column; gap: 10px; } .filter-actions { flex-direction: column; } }
</style>
