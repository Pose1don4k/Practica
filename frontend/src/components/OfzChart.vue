<template>
  <div ref="chartRef" class="chart-box"></div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue';
import * as echarts from 'echarts';

// Принимаем данные и ЦВЕТА 
const props = defineProps({
  primarySeries: { type: Object, required: true },
  secondarySeries: { type: Object, required: true },
  themeColors: {
    type: Object,
    default: () => ({
      primaryUp: '#ff4d4d',    // Красный рост 
      primaryDown: '#cc0000',  // Красное падение
      secondaryUp: '#ffb3e6',  // Розовый рост 
      secondaryDown: '#ff66c2' // Розовое падение
    })
  }
});

const chartRef = ref(null);
let chartInstance = null;

const renderChart = () => {
  if (chartInstance != null) {
    chartInstance.dispose();
  }
  chartInstance = echarts.init(chartRef.value);

  const formatCandles = (dataArray) => {
    return dataArray.map(item => {
      const [, month, day] = item.date.split('-'); 
      return { name: `${day}-${month}`, value: [item.open, item.close, item.low, item.high] };
    });
  };

  const longestSeries = props.primarySeries.data.length > props.secondarySeries.data.length ? props.primarySeries.data : props.secondarySeries.data;
  const xAxisData = longestSeries.map(item => {
    const [, month, day] = item.date.split('-');
    return `${day}.${month}`;
  });

  const option = {
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
    grid: { left: '5%', right: '5%', bottom: '15%' }, 
    xAxis: { type: 'category', data: xAxisData, boundaryGap: true },
    yAxis: { type: 'value', scale: true },
    dataZoom: [
      { type: 'inside', start: 0, end: 100 },
      { show: true, type: 'slider', bottom: '0%', start: 0, end: 100 }
    ],
    series: [
      {
        name: `Год ${props.secondarySeries.year} (Прошлый)`,
        type: 'candlestick',
        data: formatCandles(props.secondarySeries.data),
        z: 1,
        // ИСПОЛЬЗУЕМ ЦВЕТА ИЗ ПРОПСОВ
        itemStyle: { 
          color: props.themeColors.secondaryUp, 
          color0: props.themeColors.secondaryDown, 
          borderColor: props.themeColors.secondaryUp, 
          borderColor0: props.themeColors.secondaryDown 
        }
      },
      {
        name: `Год ${props.primarySeries.year} (Выбранный)`,
        type: 'candlestick',
        data: formatCandles(props.primarySeries.data),
        z: 2,
        // ИСПОЛЬЗУЕМ ЦВЕТА ИЗ ПРОПСОВ
        itemStyle: { 
          color: props.themeColors.primaryUp, 
          color0: props.themeColors.primaryDown, 
          borderColor: props.themeColors.primaryUp, 
          borderColor0: props.themeColors.primaryDown 
        }
      }
    ]
  };

  chartInstance.setOption(option);
};

// Если данные обновились - перерисовываем график
watch(() => props.primarySeries, () => {
  nextTick(() => { renderChart(); });
}, { deep: true });

onMounted(() => {
  renderChart();
  window.addEventListener('resize', () => {
    if (chartInstance) chartInstance.resize();
  });
});
</script>

<style scoped>
.chart-box {
  width: 100%;
  height: 400px;
}
</style>