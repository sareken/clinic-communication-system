import socket
import sys
import threading

HOST = '127.0.0.1'
PORT = 12345
BUFFER_SIZE = 1024

# Sunucudan gelen mesajları dinleyen fonksiyon
def receive_messages(sock):
    while True:
        try:
            data = sock.recv(BUFFER_SIZE)
            if not data:
                break
            print(f"\n{data.decode()}")
            print(">> ", end="", flush=True)
        except:
            break

# TCP istemcisi başlatılır (Doktor veya Hasta)
def run_tcp_client(client_type):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))
        s.send(f"{client_type},TCP".encode())

        threading.Thread(target=receive_messages, args=(s,), daemon=True).start()

        while True:
            msg = input(">> ")
            if msg.lower() in ["exit", "çık", "quit"]:
                print("Bağlantı sonlandırıldı.")
                s.close()
                break
            s.send(msg.encode())

    except Exception as e:
        print(f"Bağlantı hatası: {e}")

# UDP istemcisi sadece Hasta için çalışır
def run_udp_client():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.sendto("Hasta,UDP".encode(), (HOST, PORT))
        response, _ = s.recvfrom(BUFFER_SIZE)
        print(f"{response.decode()}")
    except Exception as e:
        print(f"UDP bağlantı hatası: {e}")

# Ana giriş
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Kullanım: python 22100011016_Client.py [Doktor/Hasta] [TCP/UDP]")
        sys.exit(1)
    client_type = sys.argv[1]
    protocol = sys.argv[2]

    if client_type == "Doktor" and protocol == "TCP":
        run_tcp_client("Doktor")
    elif client_type == "Hasta" and protocol == "TCP":
        run_tcp_client("Hasta")
    elif client_type == "Hasta" and protocol == "UDP":
        run_udp_client()
    else:
        print("Geçersiz giriş. Örnek: python 22100011016_Client.py Hasta TCP")
