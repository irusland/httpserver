import socket
import select


class Chat:
    def __init__(self, host='', port=12345):
        self.server = socket.socket()
        self.addr = (host, port)

        self.poller = select.epoll()
        self.conns = {}

    def __enter__(self):
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(self.addr)
        self.server.listen()
        self.server.setblocking(False)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.poller.close()
        self.server.close()
        return False

    def run(self):
        self.conns[self.server.fileno()] = self.server
        self.poller.register(self.server.fileno(), select.EPOLLIN)

        while True:
            for (fileno, event) in self.poller.poll(1.0):
                if fileno == self.server.fileno():
                    self._accept(self.server)
                elif event & select.EPOLLIN:
                    self._read(self.conns[fileno])

    def _accept(self, sock):
        (client, addr) = sock.accept()
        self.conns[client.fileno()] = client
        print(f'Connected {addr}')

        client.setblocking(False)
        self.poller.register(client.fileno(), select.EPOLLIN | select.EPOLLET)

    def _read(self, sock):
        while True:
            try:
                data = sock.recv(1)
            except BlockingIOError:
                break

            if data:
                for conn in self.conns.values():
                    if conn not in (sock, self.server):
                        try:
                            conn.sendall(data)
                        except Exception:
                            pass
            else:
                print(f'Disconnected {sock.getpeername()}')
                self.poller.unregister(sock.fileno())
                del self.conns[sock.fileno()]
                sock.close()


if __name__ == '__main__':
    with Chat() as chat:
        chat.run()
