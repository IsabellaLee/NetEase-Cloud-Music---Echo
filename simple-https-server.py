# taken from http://www.piware.de/2011/01/creating-an-https-server-in-python/
# generate server.xml with the following command:
#    openssl req -new -x509 -keyout server.pem -out server.pem -days 365 -nodes
# run as follows:
#    python simple-https-server.py
# then in your browser, visit:
#    https://localhost:4443

#import BaseHTTPServer, SimpleHTTPServer
#import ssl
#
#httpd = BaseHTTPServer.HTTPServer(('localhost', 4443), SimpleHTTPServer.SimpleHTTPRequestHandler)
#httpd.socket = ssl.wrap_socket (httpd.socket, certfile='./server.pem', server_side=True)
#httpd.serve_forever()


#import SimpleHTTPServer
#import SocketServer
#class myHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
#   def do_GET(self):
#       print self.path
#       self.send_response(303)
##       new_path = '%s%s'%('http://google.com', self.path)
##       self.send_header('Location', new_path)
##       self.send_header('Location','https://m1.jixun.moe/32507038/128000/c0430b03d66ca4f7dc6427422b41512329adb0a49fb6a563329b03514b508633')
#       self.send_header('Location','http://m2.music.126.net/VTDSXL9MorC7MqshbF39RA==/3250156393257615.mp3')
##       self.send_header('Location','https://archive.org/download/plpl011/plpl011_05-johnny_ripper-rain.mp3')
#       self.end_headers()
#
#PORT = 8000
#handler = SocketServer.TCPServer(("", PORT), myHandler)
#print "serving at port 8000"
#handler.serve_forever()

import SimpleHTTPServer
import SocketServer

PORT = 8000

Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
Handler.extensions_map.update({
    '.webapp': 'application/x-web-app-manifest+json',
});

httpd = SocketServer.TCPServer(("", PORT), Handler)

print "Serving at port", PORT
httpd.serve_forever()
