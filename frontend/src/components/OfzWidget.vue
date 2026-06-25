<template>
  <div class="ofz-widget-container">
    
    <WidgetHeader 
      v-model="selectedYear" 
      :isLoading="isLoading" 
      @fetch-data="fetchData" 
    />

    <div v-if="isError" class="error-message">Сервис недоступен</div>
    
    <div v-else-if="isLoading" class="loading-message">Загрузка данных...</div>
    
    <div v-else-if="isFullyEmpty" class="info-message">
      Торговые данные отсутствуют как за {{ selectedYear }} год, так и за прошлый {{ selectedYear - 1 }} год.
    </div>

    <div v-else-if="apiData">
      
      <div v-if="partialWarningMessage" class="warning-banner">
        Внимание: {{ partialWarningMessage }}
      </div>

      <OfzChart 
        :primarySeries="apiData.primary_series"
        :secondarySeries="apiData.secondary_series"
        :themeColors="customColors" 
      />
    </div>
    
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import WidgetHeader from './WidgetHeader.vue';
import OfzChart from './OfzChart.vue';

const currentYear = new Date().getFullYear();
const selectedYear = ref(currentYear);
const isError = ref(false);
const isLoading = ref(false);
const isFullyEmpty = ref(false); // Флаг полного отсутствия данных
const partialWarningMessage = ref(''); // Текст предупреждения о конкретном годе
const apiData = ref(null);

// Палитра цветов для графиков
const customColors = {
  primaryUp: '#ff4d4d',   
  primaryDown: '#cc0000', 
  secondaryUp: '#ffb3e6', 
  secondaryDown: '#ff66c2'
};

const fetchData = async () => {
  isLoading.value = true;
  isError.value = false;
  isFullyEmpty.value = false;
  partialWarningMessage.value = '';
  apiData.value = null;

  try {
    const response = await fetch(`http://127.0.0.1:8000/api/v1/ofz/candles?year=${selectedYear.value}`);
    if (!response.ok) throw new Error('Сбой при получении данных');

    const data = await response.json();
    
    // Анализируем наполненность массивов данных, которые прислал бэкенд
    const hasPrimary = data.primary_series.data.length > 0;
    const hasSecondary = data.secondary_series.data.length > 0;
    
    const pYear = data.primary_series.year;
    const sYear = data.secondary_series.year;

    if (!hasPrimary && !hasSecondary) {
      // Сценарий 1: Данных нет вообще (например, глубокое будущее)
      isFullyEmpty.value = true;
    } else {
      // Сценарий 2: Данные есть (хотя бы частично), передаем их графику
      apiData.value = data;

      // Сценарий 3: Выясняем, по какому именно году данные отсутствуют
      if (!hasPrimary) {
        partialWarningMessage.value = `данные отсутствуют за выбранный ${pYear} год.`;
      } else if (!hasSecondary) {
        partialWarningMessage.value = `данные отсутствуют за прошлый ${sYear} год.`;
      }
    }
  } catch (error) {
    console.error('Ошибка виджета ОФЗ:', error);
    isError.value = true;
  } finally {
    isLoading.value = false;
  }
};

onMounted(() => {
  fetchData();
});
</script>

<style scoped>
.ofz-widget-container {
  font-family: Arial, sans-serif;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px;
  background: #fff;
  max-width: 900px;
  margin: 0 auto;
}
.error-message { height: 400px; display: flex; align-items: center; justify-content: center; color: #d32f2f; font-weight: bold; background-color: #ffebee; border-radius: 4px; }
.loading-message { height: 400px; display: flex; align-items: center; justify-content: center; color: #666; }
.info-message { height: 400px; display: flex; align-items: center; justify-content: center; color: #1976d2; font-weight: bold; background-color: #e3f2fd; border-radius: 4px; }

/* Стиль для нового информативного баннера */
.warning-banner {
  padding: 10px 14px;
  background-color: #fffde7; /* Легкий пастельный желтый */
  border: 1px solid #fff59d;
  border-radius: 4px;
  color: #f57f17; /* Насыщенный янтарный цвет текста */
  font-weight: 500;
  margin-bottom: 12px;
  font-size: 0.95em;
}
</style>