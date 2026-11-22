# Backend Project Team 4

Інструкція з локального розгортання та запуску проєкту Teach App.

## Вимоги

Перед початком роботи переконайтеся, що встановлено:

- Java JDK 17
- Apache Maven
- Node.js 16
- npm
- Docker Desktop (для запуску MySQL)

## 1. Налаштування бази даних MySQL

Для запуску бази даних використовується Docker.

Виконайте команду:

```bash
docker run -d --name teach-mysql \
  -e MYSQL_ROOT_PASSWORD=root \
  -e MYSQL_DATABASE=teach_db \
  -p 3306:3306 \
  mysql:8.0
```

Перевірити стан контейнера можна командою:

```bash
docker ps
```

Якщо порт `3306` вже зайнятий, використайте інший локальний порт, наприклад `3307`:

```bash
docker run -d --name teach-mysql \
  -e MYSQL_ROOT_PASSWORD=root \
  -e MYSQL_DATABASE=teach_db \
  -p 3307:3306 \
  mysql:8.0
```

У такому випадку потрібно також змінити порт у `DATASOURCE_URL` на `3307`.

## 2. Запуск Backend

Backend запускається за допомогою Java 17 та Maven.

### 2.1. Налаштування змінних оточення

Для підключення до MySQL необхідно задати такі змінні:

| Змінна | Значення |
|---|---|
| DATASOURCE_URL | jdbc:mysql://localhost:3306/teach_db?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=UTC |
| DATASOURCE_USER | root |
| DATASOURCE_PASSWORD | root |

### Windows (PowerShell)

Перейдіть до директорії Backend:

```powershell
cd backend
```

Задайте змінні оточення:

```powershell
$env:DATASOURCE_URL="jdbc:mysql://localhost:3306/teach_db?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=UTC"
$env:DATASOURCE_USER="root"
$env:DATASOURCE_PASSWORD="root"
```

Зберіть проєкт:

```powershell
mvn clean package -DskipTests
```

Запустіть Backend:

```powershell
java -jar target/dev.war
```

### Linux / macOS (Bash)

Перейдіть до директорії Backend:

```bash
cd backend
```

Задайте змінні оточення:

```bash
export DATASOURCE_URL="jdbc:mysql://localhost:3306/teach_db?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=UTC"
export DATASOURCE_USER="root"
export DATASOURCE_PASSWORD="root"
```

Зберіть проєкт:

```bash
mvn clean package -DskipTests
```

Запустіть Backend:

```bash
java -jar target/dev.war
```

### Перевірка Backend

Після успішного запуску Backend має бути доступний за адресою:

http://localhost:8080/dev

Переконайтеся, що сервер запустився без помилок та може підключитися до бази даних MySQL.

## 3. Запуск Frontend

Frontend запускається за допомогою Node.js та npm.

### 3.1. Налаштування адреси Backend

Файл конфігурації:

`frontend/src/config/ApplicationConfig.js`

Він повинен містити:

```javascript
export const ROOT_SERVER =
  process.env.REACT_APP_ROOT_SERVER || "http://localhost:8080";

export const ROOT_URI = "/dev";

export const BASE_URL = ROOT_SERVER + ROOT_URI;
```

За замовчуванням Frontend використовує Backend за адресою:

`http://localhost:8080/dev`

За необхідності адресу можна змінити через змінну оточення `REACT_APP_ROOT_SERVER`.

### Windows (PowerShell)

Перейдіть до директорії Frontend:

```powershell
cd frontend
```

Якщо використовується Node.js 17 або новіша версія, задайте:

```powershell
$env:NODE_OPTIONS="--openssl-legacy-provider"
```

Встановіть залежності:

```powershell
npm install --legacy-peer-deps
```

Запустіть Frontend:

```powershell
npm start
```

### Linux / macOS (Bash)

Перейдіть до директорії Frontend:

```bash
cd frontend
```

Задайте параметр OpenSSL:

```bash
export NODE_OPTIONS="--openssl-legacy-provider"
```

Встановіть залежності:

```bash
npm install --legacy-peer-deps
```

Запустіть Frontend:

```bash
npm start
```

### Перевірка Frontend

Після успішного запуску сайт буде доступний за адресою:

http://localhost:3000/dev

Переконайтеся, що сайт відкривається та успішно отримує дані від Backend.

## 4. Змінні оточення

У корені репозиторію або у відповідних директоріях можна використовувати файл `.env.example` як шаблон налаштувань.

Основні змінні:

```env
# MySQL configuration
MYSQL_ROOT_PASSWORD=root
MYSQL_DATABASE=teach_db
MYSQL_PORT=3306

# Backend datasource configuration
DATASOURCE_URL=jdbc:mysql://localhost:3306/teach_db?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=UTC
DATASOURCE_USER=root
DATASOURCE_PASSWORD=root

# Frontend API configuration
REACT_APP_ROOT_SERVER=http://localhost:8080
```

Для локального запуску необхідно задати відповідні змінні оточення згідно з інструкціями вище.

**Важливо:** `.env.example` є лише шаблоном. Реальні паролі та конфіденційні налаштування не повинні зберігатися в Git-репозиторії. Файл `.env` потрібно додати до `.gitignore`.

## 5. Порядок запуску всього проєкту

Для коректної роботи застосунку дотримуйтеся такого порядку:

1. Запустити Docker Desktop.
2. Запустити контейнер MySQL.
3. Переконатися, що база даних `teach_db` доступна.
4. Запустити Backend через Maven та Java.
5. Перевірити доступність Backend за адресою `http://localhost:8080/dev`.
6. Запустити Frontend через npm.
7. Відкрити сайт за адресою `http://localhost:3000/dev`.
8. Перевірити отримання даних із Backend.

## 6. Зупинка застосунку

Для зупинки Backend та Frontend натисніть `Ctrl + C` у відповідних терміналах.

Для зупинки контейнера MySQL виконайте:

```bash
docker stop teach-mysql
```

Для повторного запуску контейнера:

```bash
docker start teach-mysql
```

## 7. Усунення можливих проблем

**MySQL не запускається:**

- Перевірте, чи не зайнятий порт `3306`.
- Переконайтеся, що Docker Desktop запущений.
- Перевірте стан контейнера командою `docker ps -a`.

**Backend не підключається до MySQL:**

- Перевірте значення `DATASOURCE_URL`.
- Переконайтеся, що MySQL працює.
- Перевірте правильність логіна та пароля.

**Backend не запускається:**

- Переконайтеся, що встановлено Java 17.
- Перевірте наявність Maven.
- Переконайтеся, що файл збірки знаходиться у `backend/target/`.

**Frontend не запускається:**

- Переконайтеся, що встановлено Node.js 16.
- Перевстановіть залежності за допомогою `npm install --legacy-peer-deps`.
- Для новіших версій Node.js перевірте параметр `NODE_OPTIONS`.

**Frontend не отримує дані від Backend:**

- Переконайтеся, що Backend запущений.
- Перевірте `ApplicationConfig.js`.
- Переконайтеся, що адреса API містить правильний контекст `/dev`.

---

**Team 4 — Teach App**
