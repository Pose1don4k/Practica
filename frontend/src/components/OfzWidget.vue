<template>
  <div class="ofz-widget-container">
    <div class="widget-header">
      <h3>Аналитика цен ОФЗ (RGBI)</h3>
      <div class="controls">
        <label for="year-select">Выберите год:</label>
        <select id="year-select" v-model="selectedYear" @change="fetchData" :disabled="isLoading">
          <option v-for="year in availableYears" :key="year" :value="year">
            {{ year }}
          </option>
        </select>
      </div>
    </div>

    <div v-if="isError" class="error-message">
      Сервис недоступен
    </div>

    <div v-else-if="isLoading" class="loading-message">
      Загрузка данных...
    </div>

    <div v-show="!isError && !isLoading" ref="chartRef" class="chart-box"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'; // Добавили nextTick
import * as echarts from 'echarts';

const chartRef = ref(null);
let chartInstance = null;

const currentYear = new Date().getFullYear();
const selectedYear = ref(currentYear);
const isError = ref(false);
const isLoading = ref(false);

const availableYears = Array.from({ length: 10 }, (_, i) => currentYear - i);

const fetchData = async () => {
  isLoading.value = true;
  isError.value = false;

  try {
    const response = await fetch(`http://127.0.0.1:8000/api/v1/ofz/candles?year=${selectedYear.value}`);
    
    if (!response.ok) {
      throw new Error('Сбой при получении данных');
    }

    const data = await response.json();
    
    // ИСПРАВЛЕНИЕ: Сначала выключаем экран загрузки, чтобы div графика появился в DOM
    isLoading.value = false;
    
    // Ждем, пока Vue физически обновит HTML-страницу и блок получит свои 100% ширины
    await nextTick();
    
    // И только теперь инициализируем и рисуем график!
    renderChart(data);

  } catch (error) {
    console.error('Ошибка виджета ОФЗ:', error);
    isError.value = true;
    isLoading.value = false; // Выключаем загрузку даже при ошибке
  }
};

const renderChart = (apiResponse) => {
  if (chartInstance != null) {
    chartInstance.dispose();
  }
  chartInstance = echarts.init(chartRef.value);

  const primary = apiResponse.primary_series;
  const secondary = apiResponse.secondary_series;

  const formatCandles = (dataArray) => {
    return dataArray.map(item => {
      const [, month, day] = item.date.split('-'); 
      return {
        name: `${day}-${month}`, 
        value: [item.open, item.close, item.low, item.high]
      };
    });
  };

  const longestSeries = primary.data.length > secondary.data.length ? primary.data : secondary.data;
  const xAxisData = longestSeries.map(item => {
    const [, month, day] = item.date.split('-');
    return `${day}.${month}`;
  });

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    grid: { left: '5%', right: '5%', bottom: '15%' }, 
    xAxis: {
      type: 'category',
      data: xAxisData,
      boundaryGap: true,
    },
    yAxis: {
      type: 'value',
      scale: true,
    },
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100
      },
      {
        show: true,
        type: 'slider',
        bottom: '0%',
        start: 0,
        end: 100
      }
    ],
    series: [
      {
        name: `Год ${secondary.year}`,
        type: 'candlestick',
        data: formatCandles(secondary.data),
        z: 1,
        itemStyle: {
          color: '#ffb3e6',
          color0: '#ff66c2',
          borderColor: '#ffb3e6',
          borderColor0: '#ff66c2'
        }
      },
      {
        name: `Год ${primary.year}`,
        type: 'candlestick',
        data: formatCandles(primary.data),
        z: 2,
        itemStyle: {
          color: '#ff4d4d',
          color0: '#cc0000',
          borderColor: '#ff4d4d',
          borderColor0: '#cc0000'
        }
      }
    ]
  };

  chartInstance.setOption(option);
};

onMounted(() => {
  fetchData();
  window.addEventListener('resize', () => {
    if (chartInstance) chartInstance.resize();
  });
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
.widget-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.controls select {
  margin-left: 8px;
  padding: 4px 8px;
}
.chart-box {
  width: 100%;
  height: 400px;
}
.error-message {
  height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #d32f2f;
  font-weight: bold;
  background-color: #ffebee;
  border-radius: 4px;
}
.loading-message {
  height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
}
</style>