def receive_unity_instruction(server_ip, server_port):    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((server_ip, server_port))
    
    server_socket.listen(1)
    print(f"Waiting for connection on {server_ip}:{server_port}")

    client_socket, client_address = server_socket.accept()
    print(f"Connected by {client_address}")
    
    data = client_socket.recv(1024)
    print(f"Received data: {data.decode('utf-8')}")
    
    client_socket.close()
    server_socket.close()

    return data.decode('utf-8')

def send_data_to_server(server_ip, server_port, message):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
        client_socket.sendto(message.encode('utf-8'), (server_ip, server_port))

def recive_data_from_server(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", port))
    print(f"UDP server listening on :{port}")
    data, addr = sock.recvfrom(1024)
    sock.close()

    return data.decode()