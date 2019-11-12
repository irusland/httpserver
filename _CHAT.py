import selectors
import socket
import select


class Chat:
    def __init__(self, host='', port=12345):
        self.server = socket.socket()
        self.addr = (host, port)
        self.poller = selectors.DefaultSelector()
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
        self.poller.register(self.server, selectors.EVENT_READ,
                             self._accept)

        while True:
            for key, mask in self.poller.select():
                callback = key.data
                callback(key.fileobj, mask)

    def _accept(self, sock, mask):
        print(sock)
        (client, addr) = sock.accept()
        self.conns[client.fileno()] = client
        print(f'Connected {addr}')

        client.setblocking(False)
        self.poller.register(client, selectors.EVENT_READ, self._read)

    def _read(self, sock, mask):
        while True:
            try:
                data = sock.recv(1)
            except (BlockingIOError, OSError):
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
