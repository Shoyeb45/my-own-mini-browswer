from io import BufferedReader
import socket
import ssl # for https, tls
from typing import Dict

open_sockets: Dict[tuple, tuple[socket.socket, BufferedReader]] = {}

class URL:

    def __init__(self, url: str):
        # Defining constants
        self.__SCHEME_HTTPS = "https"
        self.__SCHEME_HTTP = "http"
        self.__SCHEME_FILE = "file"
        self.__HTTP_VERSION = "HTTP/1.1"
        self.__SCHEME_DATA = "data"
        self.__SCHEME_VIEW_SOURCE = "view-source"
        self.__CRLF = "\r\n"

        splitted_url = url.split("://", 1)
        if len(splitted_url) <= 1:
            # check for data scheme
            self.scheme, url = url.split(":", 1)
        else:
            self.scheme, url = splitted_url
            if self.scheme.startswith(self.__SCHEME_VIEW_SOURCE):
                self.scheme, scheme = self.scheme.split(":", 1)
                url = scheme + "://" + url

        # check support of the scheme
        assert self.scheme in [self.__SCHEME_HTTPS, self.__SCHEME_HTTP, self.__SCHEME_FILE, self.__SCHEME_DATA, self.__SCHEME_VIEW_SOURCE]

        if self.scheme == self.__SCHEME_HTTP:
            # HTTP Uses 80 as default port
            self.port = 80
        elif self.scheme == self.__SCHEME_HTTPS:
            # HTTPS uses 443 as default port
            self.port = 443
        elif self.scheme == self.__SCHEME_FILE:
            self.path = url
            return
        elif self.scheme == self.__SCHEME_DATA:
            self.mime_type, self.content = url.split(",", 1)
            return
        elif self.scheme == self.__SCHEME_VIEW_SOURCE:
            self.inner_url = url
            return

        if "/" not in url:
            url = "/" + url

        # now we have url with host + path, /shoyeb.vercel.app/index.html
        self.host, url = url.split("/", 1)

        # if there is port present in url, extract it
        if ":" in self.host:
            self.host, port = self.host.split(":", 1)
            self.port = int(port)
        
        self.path = "/" + url

    def get_socket(self, host: str, port: int) -> tuple[socket.socket, BufferedReader]:
        global open_sockets

        key = (host, port)

        if key in open_sockets:
            return open_sockets[key]
        
        s = socket.socket(
            # the socket family which tells how to find another computer
            family=socket.AF_INET,
            # type of socket which describes the conversation type that;s going to happen
            type=socket.SOCK_STREAM, # can send arbitary amounts of data
            # protocol, the steps by which the two computers will establish communincation
            proto=socket.IPPROTO_TCP
        )

        # note it accepts tuple
        s.connect((self.host, self.port))

        if self.scheme == self.__SCHEME_HTTPS:
            ctx = ssl.create_default_context()
            # This library will handle the encrypting and connection to the correct host
            s = ctx.wrap_socket(s, server_hostname=self.host)
       
        f = s.makefile("rb")

        open_sockets[key] = (s, f)

        return open_sockets[key]
    def request(self):
        # Handle scheme file differently
        if self.scheme == self.__SCHEME_FILE:
            try:
                content = ""
                with open(self.path, "r") as file:
                    content = file.read()
                
                return content 
            except Exception as e:
                print(e)
                return "No File Exists"
        
        if self.scheme == self.__SCHEME_DATA:
            return self.content
        
        if self.scheme == self.__SCHEME_VIEW_SOURCE:
            url = URL(self.inner_url)
            content = url.request()
            return content
        

        # Now let's send some request to server
        # First add headers
        request = "GET {} {}\r\n".format(self.path, self.__HTTP_VERSION)
        request += self.__add_header("Host", self.host)
        request += self.__add_header("Connection", "keep-alive")
        request += self.__add_header("User-Agent", "mini-browser")
        request += self.__CRLF

        s, response = self.get_socket(self.host, self.port)

        try:
            s.send(request.encode("utf-8")) # send the data as bytes
        except BrokenPipeError as e:
            del open_sockets[(self.host, self.port)]
            return self.request()

        # reading the response from the server
        # response = s.makefile("rb", encoding="utf8", newline="\r\n")

        statusline = response.readline()
        version, status, explanation = statusline.split(b" ", 2)

        response_headers = {}

        while True:
            line = response.readline()
            if line == b"\r\n": break
            header, value = line.split(b":", 1)
            response_headers[header.decode("utf-8").casefold()] = value.decode("utf-8").strip().casefold()

            assert "transfer-encoding" not in response_headers
            assert "content-encoding" not in response_headers
        
        assert "content-length" in response_headers

        content_length = int(response_headers["content-length"])

        # read only specified bytes
        content = response.read(content_length)
        print(response_headers["content-type"])
        # delete the socket, if server sends connection: close
        if not "connection" in response_headers or response_headers["connection"] == "close":
            del open_sockets[(self.host, self.port)]

        return self.decode_content(content, response_headers["content-type"])
    
    def __add_header(self, key: str, val: str):
        '''
        It returns the header in `key: value` format
        '''
        return "{}: {}{}".format(key, val, self.__CRLF)
    
    def decode_content(self, content: bytes, contentType: str):
        if contentType.startswith("audio"):
            # handle audio type
            return "Content-Type: audio not implemented\n"
        
        if contentType.startswith("application"):
            # handle application type
            return "Content-Type: application not implemented\n"
            
        if contentType.startswith("image"):
            return "Content-Type: image not implemented\n"

        if contentType.startswith("multipart"):
            return "Content-Type: multipart not implemented\n"
            
        if contentType.startswith("text"):
            return content.decode("utf-8")

        if contentType.startswith("video"):
            return "Content-Type: video not implemented\n"
        
        return "Content-Type: application/vnd not implemented\n"
    def show(self, body: str):
        if self.scheme == self.__SCHEME_VIEW_SOURCE:
            print(body)
            return
        
        in_tag = False
        i = 0
        while i < len(body):
            c = body[i]
            if c == "<":
                in_tag = True
            elif c == ">":
                in_tag = False
            elif not in_tag:
                if c == "&":
                    idx = body.find(";", i)
                    entity = body[i : i + (idx - i + 1)]
                    if entity == "&lt;":
                        print("<", end="")
                    elif entity == "&gt;":
                        print(">", end="")
                    elif entity == "&nbsp;":
                        print(" ", end="")

                    i += (idx - i)
                else:
                    print(c, end="")
            i += 1



