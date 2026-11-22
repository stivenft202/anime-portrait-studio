# Anime Half Portrait Studio — versión independiente de Unity.
# Uso:  python3 servidor.py
# Abre el creador en el navegador (http://localhost:8765). Sin internet,
# sin Unity, sin instalar nada más: solo Python 3.
import http.server, os, threading, webbrowser

AQUI = os.path.dirname(os.path.abspath(__file__))
PUERTO = 8765

class Manejador(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=AQUI, **kw)
    def log_message(self, *a):
        pass

if __name__ == '__main__':
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', PUERTO), Manejador)
    print(f'Portrait Studio abierto en http://localhost:{PUERTO}  (Ctrl+C para cerrar)')
    threading.Timer(0.6, lambda: webbrowser.open(f'http://localhost:{PUERTO}')).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print('\nCerrado.')
