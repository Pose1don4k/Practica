# --- Этап 1: Сборка проекта (Build stage) ---
FROM node:20-alpine as build-stage
WORKDIR /app

# Копируем package.json и устанавливаем зависимости
COPY package*.json ./
RUN npm install

# Копируем весь код и собираем продакшен-версию компонента
COPY . .
RUN npm run build

# --- Этап 2: Раздача статики (Production stage) ---
FROM nginx:stable-alpine as production-stage

# Копируем собранные файлы из первого этапа в папку Nginx
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Открываем стандартный веб-порт
EXPOSE 80

# Запускаем Nginx
CMD ["nginx", "-g", "daemon off;"]