<template>
  <div class="widget-header">
    <h3>{{ title }}</h3>
    <div class="controls">
      <label for="year-input">Введите год:</label>
      <input 
        id="year-input" 
        type="number" 
        :value="modelValue" 
        @input="$emit('update:modelValue', $event.target.value)"
        @change="$emit('fetch-data')"
        :disabled="isLoading"
        placeholder="Например, 2026"
      />
    </div>
  </div>
</template>

<script setup>
// Принимаем данные от родителя
defineProps({
  title: { type: String, default: 'Аналитика цен ОФЗ' },
  modelValue: { type: [Number, String], required: true },
  isLoading: { type: Boolean, default: false }
});

// Сообщаем родителю о действиях пользователя
defineEmits(['update:modelValue', 'fetch-data']);
</script>

<style scoped>
.widget-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.controls input {
  margin-left: 8px;
  padding: 4px 8px;
  width: 80px;
}
</style>