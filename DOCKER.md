# Запуск у Docker

## Збірка образів

```bash
docker build -t teach-backend ./backend
docker build -t teach-frontend ./frontend
```

Адреса бекенда записується у фронтенд під час збірки (за замовчуванням `http://localhost:8080`):

```bash
docker build -t teach-frontend --build-arg REACT_APP_ROOT_SERVER=http://my-host:8080 ./frontend
```

## Запуск

```bash
docker network create teach-net

docker run -d --name teach-mysql --network teach-net \
  -e MYSQL_ROOT_PASSWORD=root -e MYSQL_DATABASE=teach_db mysql:8.0

docker run -d --name teach-backend --network teach-net -p 8080:8080 \
  -e DATASOURCE_URL="jdbc:mysql://teach-mysql:3306/teach_db?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=UTC" \
  -e DATASOURCE_USER=root -e DATASOURCE_PASSWORD=root \
  teach-backend

docker run -d --name teach-frontend -p 3000:80 teach-frontend
```

- Backend: http://localhost:8080/dev
- Frontend: http://localhost:3000/dev
