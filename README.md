# Media Streaming Service

Репозиторий содержит код сервиса потоковой передачи мультимедиа с использованием gRPC и SQLite на Python.

## 📦 Содержание проекта

- `media.proto` — описание gRPC API.  
- `media_pb2.py`, `media_pb2_grpc.py` — сгенерированные файлы протоколов.  
- `server.py` — реализация gRPC-сервера.  
- `client.py` — клиент с поддержкой CLI и интерактивного меню.  
- `media.db` — база данных SQLite (создаётся автоматически).  
- `storage/` — папка для хранения загруженных файлов.  

## 🚀 Быстрый старт

### 1. Клонирование репозитория
```bash
git clone https://github.com/your-username/media-streaming-service.git
cd media-streaming-service
```
### 2. Установка зависимостей
Рекомендуется создать виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate        # Linux/MacOS
venv\Scripts\activate           # Windows PowerShell
```
Установите зависимости:
```bash
pip install grpcio grpcio-tools
```
SQLite входит в стандартную библиотеку Python.

### 3. Генерация gRPC-кода
После правок media.proto выполните:
```bash
python -m grpc_tools.protoc \
    --proto_path=. \
    --python_out=. \
    --grpc_python_out=. \
    media.proto
```
Будут созданы/обновлены файлы media_pb2.py и media_pb2_grpc.py.

### 4. Запуск сервера
1. Убедитесь, что есть папка для хранения:
```bash
mkdir -p storage
```
2. Запустите сервер:
```bash
python server.py
```
Сервер будет слушать порт 50051 и автоматически инициализирует базу media.db.

### 5. Использование клиента
#### 5.1. Интерактивное меню
Запустите без аргументов:
```bash
python client.py
```
Появится меню с выбором:
1. Загрузить файл
2. Стримить файл
3. Посмотреть статистику
4. Список видео

#### 5.2. CLI-режим
```bash
# Загрузка
python client.py upload /path/to/video.mp4

# Стриминг и сохранение
python client.py stream <content_id> downloaded.mp4

# Статистика просмотров
python client.py stats <content_id>

# Список загруженного контента
python client.py list
```

## 🗂 Структура таблицы contents

| Поле          | Тип      | Описание                          |
| ------------- | -------- | --------------------------------- |
| `id`          | INTEGER  | Уникальный идентификатор контента |
| `title`       | TEXT     | Оригинальное имя файла            |
| `path`        | TEXT     | Путь к файлу в папке `storage/`   |
| `uploaded_at` | DATETIME | Дата и время загрузки             |

