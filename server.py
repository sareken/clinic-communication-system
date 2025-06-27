"""
- Doktorlar sadece TCP protokolü üzerinden sisteme bağlanır.
- Hastalar iki farklı şekilde bağlanabilir:
    ▪ TCP üzerinden bağlanan hastalar 'randevulu hasta' olarak kabul edilir.
    - TCP, bağlantı odaklı ve karşılıklı veri alışverişine uygun olduğundan randevulu hastalar için uygundur.
    ▪ UDP üzerinden bağlanan hastalar 'randevusuz hasta' olarak kabul edilir.
    - UDP ise bağlantısız ve hafif bir yapı sunduğundan randevusuz hastaların pasif bekleme modeli için daha uygundur.
-Randevusuz (UDP) hastalar bağlantısız olduğu için onay istenmeden sistem tarafından otomatik kabul edilir.

Not:
Bu projede başlangıçta "ilk iki hasta randevulu kabul edilsin" yaklaşımı uygulanacaktı.
Ancak bir arkadaşımın önerisiyle bu yöntem yerine, **bağlantı türüne göre (TCP/UDP) hasta türü
belirlenmesi** daha sistematik bulundu ve tercih edildi.

  -----python 22100011016_Server.py----------------
  -----python 22100011016_Client.py Doktor TCP-----
  -----python 22100011016_Client.py Hasta TCP------
  -----python 22100011016_Client.py Hasta UDP------
"""
import socket
import threading
import select
import time
import os

# Sunucu IP ve Port bilgileri
HOST = '127.0.0.1'
PORT = 12345
BUFFER_SIZE = 1024

# Bağlı doktorlar ve hastalar
connected_doctors = []
connected_patients_randevulu = []
connected_patients_randevusuz = []
hasta_gecmisi = {}
patient_counter = 0

# En az hasta almış doktoru döndürür
def get_doctor_with_least_patients():
    counts = {d['name']: hasta_gecmisi.get(d['name'], 0) for d in connected_doctors}
    return min(counts, key=counts.get) if counts else None

# En çok hasta almış doktoru döndürür
def get_doctor_with_most_patients():
    counts = {d['name']: hasta_gecmisi.get(d['name'], 0) for d in connected_doctors}
    return max(counts, key=counts.get) if counts else None

# Doktor komutlarını işleyen fonksiyon
def handle_doctor_commands(doctor_name, conn):
    while True:
        try:
            conn.send(b">> ")
            message = conn.recv(BUFFER_SIZE).decode().strip()
            if message == "Hasta Kabul":
                patient = None

                # Öncelik randevulu hastalarda
                if connected_patients_randevulu:
                    if doctor_name != get_doctor_with_least_patients():
                        conn.send(f"Sizden önce başka doktor hasta almalı.\n".encode())
                        continue
                    patient = connected_patients_randevulu.pop(0)

                #Randevulu yoksa randevusuz hasta kontrolü
                elif connected_patients_randevusuz:
                    if doctor_name != get_doctor_with_least_patients():
                        conn.send(f"Sizden önce başka doktor hasta almalı.\n".encode())
                        continue
                    patient = connected_patients_randevusuz.pop(0)

                else:
                    # Diğer doktorun sırası doluysa kalan hastayı çek
                    most_loaded = get_doctor_with_most_patients()
                    if most_loaded and most_loaded != doctor_name:
                        if connected_patients_randevulu:
                            patient = connected_patients_randevulu.pop(0)
                        elif connected_patients_randevusuz:
                            patient = connected_patients_randevusuz.pop(0)

                if not patient:
                    conn.send("Bekleyen hasta bulunmamaktadır.\n".encode())
                    continue

                patient_conn = patient['conn']
                patient_name = patient['name']

                conn.send(f"{patient_name} çağırıldı. Onay bekleniyor...\n".encode())
                if patient_conn:
                    patient_conn.send(f"{doctor_name} sizi çağırıyor. Randevuyu kabul etmek için 'K' yazınız.\n".encode())

                # Hasta yanıt bekleme fonksiyonu (10 saniye içinde yanıt yoksa zaman aşımı)
                def wait_for_accept():
                    try:
                        if patient_conn:
                            patient_conn.settimeout(10)
                            response = patient_conn.recv(BUFFER_SIZE).decode().strip()
                            if response.upper() == "K":
                                conn.send(f"{patient_name} randevuyu kabul etti.\n".encode())
                                patient_conn.send(f"{patient_name} -> {doctor_name} randevusunu kabul etti.\n".encode())
                                patient_conn.send("Geçmiş olsun! Bağlantınız sonlandırılıyor...\n".encode())
                                patient_conn.close()
                                print(f"[✓] {patient_name} -> {doctor_name} eşleşti.")
                                print(f"[×] {patient_name} ayrıldı.")
                                hasta_gecmisi[doctor_name] = hasta_gecmisi.get(doctor_name, 0) + 1
                                # Hasta kalmadıysa sistemi kapat
                                if not connected_patients_randevulu and not connected_patients_randevusuz:
                                    for d in connected_doctors:
                                        d['conn'].send("Tüm hastalar bitmiştir. Sistem kapanıyor.\n".encode())
                                        d['conn'].close()
                                    print("Tüm hastalar bitti. Sunucu kapatılıyor.")
                                    os._exit(0)
                            else:
                                raise Exception("Geçersiz yanıt")
                        else:
                            conn.send(f"{patient_name} bağlantısız UDP hasta. Otomatik kabul ediliyor...\n".encode())
                            print(f"[✓] {patient_name} (UDP) -> {doctor_name} eşleşti (otomatik).\n[×] {patient_name} ayrıldı.")
                            hasta_gecmisi[doctor_name] = hasta_gecmisi.get(doctor_name, 0) + 1
                            if not connected_patients_randevulu and not connected_patients_randevusuz:
                                for d in connected_doctors:
                                    d['conn'].send("Tüm hastalar bitmiştir. Sistem kapanıyor.\n".encode())
                                    d['conn'].close()
                                print("Tüm hastalar bitti. Sunucu kapatılıyor.")
                                os._exit(0)
                    except:
                        conn.send(f"{patient_name} yanıt vermedi. Diğer hasta çağırılıyor...\n".encode())
                        if patient_conn:
                            try:
                                patient_conn.send("Yanıt verilmediği için bağlantınız kesildi.\n".encode())
                                patient_conn.close()
                            except:
                                pass
                        print(f"[×] {patient_name} zaman aşımıyla ayrıldı.")

                threading.Thread(target=wait_for_accept).start()

        except:
            break

# TCP bağlantısı kuran istemcileri (doktor/hasta) yönetir
def handle_client_tcp(conn, addr):
    global patient_counter
    try:
        client_info = conn.recv(BUFFER_SIZE).decode().split(',')
        client_type = client_info[0]
        protocol = client_info[1]

        if client_type == 'Doktor':
            doctor_name = f"Doktor{len(connected_doctors)+1}"
            connected_doctors.append({'name': doctor_name, 'conn': conn})
            print(f"[+] {doctor_name} bağlandı ({addr}) [{protocol}]")
            conn.send(f"{doctor_name} olarak sisteme bağlandınız.\n".encode())
            threading.Thread(target=handle_doctor_commands, args=(doctor_name, conn)).start()

        elif client_type == 'Hasta':
            if not connected_doctors:
                conn.send("Sistemde doktor yok. Bağlantı sonlandırılıyor.\n".encode())
                conn.close()
                return

            patient_counter += 1
            patient_name = f"Hasta{patient_counter}"

            if protocol == 'TCP':
                connected_patients_randevulu.append({'name': patient_name, 'conn': conn})
                print(f"[+] (RANDEVULU) {patient_name} bağlandı ({addr}) [{protocol}]")
                conn.send(f"Hoşgeldiniz {patient_name}! (Randevulu Hasta)\n".encode())
            else:
                connected_patients_randevusuz.append({'name': patient_name, 'conn': conn})
                print(f"[+] (RANDEVUSUZ) {patient_name} bağlandı ({addr}) [{protocol}]")
                conn.send(f" Hoşgeldiniz {patient_name}! (Randevusuz Hasta)\n".encode())

            for d in connected_doctors:
                try:
                    d['conn'].send(f"{patient_name} sisteme bağlandı [{protocol}]\n".encode())
                except:
                    pass
    except Exception as e:
        print(f"[HATA] {e}")
        conn.close()

# Sunucu başlatma işlemini gerçekleştirir
def start_server():
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.bind((HOST, PORT))
    tcp_socket.listen()
    print(f"[TCP Dinleniyor] {HOST}:{PORT}")

    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind((HOST, PORT))
    print(f"[UDP Dinleniyor] {HOST}:{PORT}")

    sockets_list = [tcp_socket, udp_socket]

    while True:
        read_sockets, _, _ = select.select(sockets_list, [], [])
        for notified_socket in read_sockets:
            if notified_socket == tcp_socket:
                conn, addr = tcp_socket.accept()
                threading.Thread(target=handle_client_tcp, args=(conn, addr)).start()
            elif notified_socket == udp_socket:
                data, addr = udp_socket.recvfrom(BUFFER_SIZE)
                message = data.decode().split(',')
                if message[0] == "Hasta":
                    global patient_counter
                    if not connected_doctors:
                        udp_socket.sendto("Sistemde doktor yok.".encode(), addr)
                    else:
                        patient_counter += 1
                        patient_name = f"Hasta{patient_counter}"
                        connected_patients_randevusuz.append({'name': patient_name, 'conn': None})
                        udp_socket.sendto(f" Hoşgeldiniz {patient_name}! (Randevusuz Hasta)".encode(), addr)
                        print(f"[+] (RANDEVUSUZ) {patient_name} UDP ile bağlandı ({addr})")

                        # Doktorlara UDP hasta bilgisini gönder
                        for d in connected_doctors:
                            try:
                                d['conn'].send(f"{patient_name} sisteme bağlandı [UDP]\n".encode())
                            except:
                                pass


if __name__ == "__main__":
    start_server()
