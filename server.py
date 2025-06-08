import os
import re
import sqlite3
from concurrent import futures

import grpc
import media_pb2, media_pb2_grpc
from google.protobuf import empty_pb2

DB_PATH = 'media.db'
STORAGE_DIR = 'storage'
os.makedirs(STORAGE_DIR, exist_ok=True)

# --- Инициализация БД ---
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()
cursor.executescript("""
CREATE TABLE IF NOT EXISTS contents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    path TEXT NOT NULL,
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS views (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_id INTEGER NOT NULL REFERENCES contents(id),
    viewed_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
""")
conn.commit()

class MediaService(media_pb2_grpc.MediaServiceServicer):

    def UploadContent(self, request_iterator, context):
        file_obj = None
        content_id = None
        for chunk in request_iterator:
            if chunk.content_id == 0 and not file_obj:
        # запомним базовое имя и «очистим» его
                original_name = os.path.basename(chunk.filename)
                safe_name = re.sub(r"[^\w\.\-]", "_", original_name)
                # создаём запись в БД
                cursor.execute(
                    "INSERT INTO contents(title, path) VALUES(?, ?)",
                    (original_name, "")
                )
                content_id = cursor.lastrowid
                # формируем путь и сохраняем его в БД
                file_path = os.path.join(STORAGE_DIR, f"{content_id}_{safe_name}")
                cursor.execute(
                    "UPDATE contents SET path = ? WHERE id = ?",
                    (file_path, content_id)
                )
                conn.commit()
                file_obj = open(file_path, 'wb')
            # пишем данные в уже открытый файл
            file_obj.write(chunk.data)
        if file_obj:
            file_obj.close()
            return media_pb2.UploadStatus(success=True, content_id=content_id, message="Uploaded")
        return media_pb2.UploadStatus(success=False, message="No data received")

    def StreamContent(self, request, context):
        # фиксируем просмотр
        cursor.execute(
            "INSERT INTO views(content_id) VALUES(?)", (request.content_id,)
        )
        conn.commit()
        # читаем файл и стримим чанками
        cursor.execute("SELECT path FROM contents WHERE id = ?", (request.content_id,))
        row = cursor.fetchone()
        if not row:
            context.abort(grpc.StatusCode.NOT_FOUND, "Content not found")
        with open(row[0], 'rb') as f:
            while True:
                data = f.read(64*1024)  # 64KB
                if not data:
                    break
                yield media_pb2.MediaChunk(content_id=request.content_id, data=data)

    def GetStatistics(self, request, context):
        cursor.execute(
            "SELECT COUNT(*) FROM views WHERE content_id = ?", (request.content_id,)
        )
        count = cursor.fetchone()[0]
        return media_pb2.Statistics(content_id=request.content_id, view_count=count)
    
    def ListContents(self, request: empty_pb2.Empty, context):
        # Получаем все записи из таблицы contents
        cursor.execute(
            "SELECT id, title, path, uploaded_at FROM contents ORDER BY uploaded_at DESC"
        )
        rows = cursor.fetchall()
        # Формируем список элементов
        items = []
        for cid, title, path, uploaded_at in rows:
            items.append(media_pb2.ContentInfo(
                content_id=cid,
                title=title,
                path=path,
                uploaded_at=uploaded_at
            ))
        # Возвращаем единым сообщением
        return media_pb2.ContentsList(items=items)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    media_pb2_grpc.add_MediaServiceServicer_to_server(MediaService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Server started on port 50051")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
