# clinic-communication-system

This project implements a simplified client-server system in Python to simulate a clinic environment where multiple doctors and patients communicate.

- The **server** listens on localhost (`127.0.0.1`) port `12345`, handling both TCP and UDP connections.
- There are two types of clients: **Doctors** and **Patients**.
- Patients can connect via TCP (appointment patients) or UDP (walk-in patients).
- Doctors connect only via TCP.
- The server manages connections, assigns user names (Doctor1, Doctor2, Hasta1, Hasta2, etc.), and handles appointment requests.

---

## Features and Implementation Details

1. **Multiple Protocol Support:**  
   - Server listens for TCP and UDP messages simultaneously using `select`.
   
2. **User Management:**  
   - The first two TCP clients connecting as doctors are named `Doktor1` and `Doktor2`.
   - Patients are assigned names sequentially (`Hasta1`, `Hasta2`, etc.) based on connection order and protocol.
   - Patients cannot connect if there are no doctors connected.

3. **Doctor-Patient Interaction:**  
   - Doctors can accept patients by typing `"Hasta Kabul"` in their TCP session.
   - The server prioritizes appointment (TCP) patients; if none are available, walk-in (UDP) patients are assigned.
   - Patients must accept the appointment within 10 seconds by sending `"K"`. Otherwise, the server calls the next patient.
   - On acceptance, both doctor and patient are notified with a confirmation message.
   - When a doctor calls a new patient, the previous patient's connection is closed with a `"Geçmiş olsun"` message.
   - When all patients are served, the server notifies doctors and shuts down.

4. **Client Scripts:**  
   - `22100011016_Client.py` takes two command line arguments:  
     - Client type: `"Doktor"` or `"Hasta"`  
     - Protocol: `"TCP"` or `"UDP"`  
   - TCP clients maintain a live session; UDP clients (only patients) communicate via datagrams.

---

## How to Run

- **Start the server:**  
  ```bash
  python 22100011016_Server.py
