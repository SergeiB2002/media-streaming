import grpc
import media_pb2, media_pb2_grpc
import os
import sys
import argparse
from google.protobuf import empty_pb2

# Настройка канала и stub
def get_stub():
    channel = grpc.insecure_channel('localhost:50051')
    return media_pb2_grpc.MediaServiceStub(channel)

stub = get_stub()

# Функции клиента
def upload(file_path):
    filename = os.path.basename(file_path)
    def gen_chunks():
        with open(file_path, 'rb') as f:
            first = True
            while True:
                data = f.read(64*1024)
                if not data:
                    break
                print(f"[CLIENT] Chunk len = {len(data)}")
                if first:
                    yield media_pb2.MediaChunk(content_id=0, data=data, filename=filename)
                    first = False
                else:
                    yield media_pb2.MediaChunk(content_id=0, data=data)
    status = stub.UploadContent(gen_chunks())
    print(f"Upload: success={status.success}, id={status.content_id}")


def stream(content_id, out_path):
    req = media_pb2.ContentRequest(content_id=content_id)
    with open(out_path, 'wb') as f:
        for chunk in stub.StreamContent(req):
            f.write(chunk.data)
    print(f"Received content saved to {out_path}")


def stats(content_id):
    req = media_pb2.ContentRequest(content_id=content_id)
    result = stub.GetStatistics(req)
    print(f"Content {result.content_id} has {result.view_count} views")

def list_contents():
    response = stub.ListContents(empty_pb2.Empty())
    # Вывод табличкой
    print(f"{'ID':<5} {'Title':<40} {'Uploaded At':<30}")
    print('-' * 60)
    for item in response.items:
        print(f"{item.content_id:<5} {item.title:<30} {item.uploaded_at:<20}")

# Интерактивное меню
def interactive_menu():
    print("Выберите действие:")
    print("1. Загрузить файл")
    print("2. Стримить файл")
    print("3. Посмотреть статистику")
    print("4. Список видео")
    choice = input("Введите номер действия: ")
    if choice == '1':
        path = input("Введите путь к файлу для загрузки: ")
        upload(path)
    elif choice == '2':
        cid = int(input("Введите content_id для стриминга: "))
        out = input("Введите путь, куда сохранить файл: ")
        stream(cid, out)
    elif choice == '3':
        cid = int(input("Введите content_id для статистики: "))
        stats(cid)
    elif choice == '4':
        list_contents()
    else:
        print("Неверный выбор. Завершение.")

# CLI-парсер как альтернативный способ использования
parser = argparse.ArgumentParser(description='Media Streaming Client')
subparsers = parser.add_subparsers(dest='cmd')

p_upload = subparsers.add_parser('upload', help='Upload a media file')
p_upload.add_argument('file_path', help='Path to local media file')

p_stream = subparsers.add_parser('stream', help='Download/stream a media file')
p_stream.add_argument('content_id', type=int, help='ID of content to stream')
p_stream.add_argument('out_path', help='Where to save the downloaded file')

p_stats = subparsers.add_parser('stats', help='Get view statistics')
p_stats.add_argument('content_id', type=int, help='ID of content to query')

p_list = subparsers.add_parser('list', help='Show list of contents')

if __name__ == '__main__':
    # Если переданы аргументы, используем CLI
    if len(sys.argv) > 1:
        args = parser.parse_args()
        if args.cmd == 'upload':
            upload(args.file_path)
        elif args.cmd == 'stream':
            stream(args.content_id, args.out_path)
        elif args.cmd == 'stats':
            stats(args.content_id)
        elif args.cmd == 'list':
            list_contents()
        else:
            parser.print_help()
    else:
        # Иначе — интерактивное меню
        interactive_menu()
