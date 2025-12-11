import socket
import ssl # for https, tls

class URL:

    def __init__(self, url: str):
        self.__HTTPS = "https"
        self.__HTTP = "http"

        self.scheme, url = url.split("://", 1)
        assert self.scheme in [self.__HTTPS, self.__HTTP]

        if self.scheme == self.__HTTP:
            # HTTP Uses 80 as default port
            self.port = 80
        elif self.scheme == self.__HTTPS:
            # HTTPS uses 443 as default port
            self.port = 443

        if "/" not in url:
            url = "/" + url
        # now we have url with host + path, /shoyeb.vercel.app/index.html
        self.host, url = url.split("/", 1)

        # if there is port present in url, extract it
        if ":" in self.host:
            self.host, port = self.host.split(":", 1)
            self.port = int(port)
        
        self.path = "/" + url

    def request(self):
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

        if self.scheme == self.__HTTPS:
            ctx = ssl.create_default_context()
            # This library will handle the encrypting and connection to the correct host
            s = ctx.wrap_socket(s, server_hostname=self.host)

        # Now let's send some request to server
        request = "GET {} HTTP/1.0\r\n".format(self.path)
        request += "Host: {}\r\n".format(self.host)
        request += "\r\n"
        s.send(request.encode("utf-8")) # send the data as bytes

        # reading the response from the server
        response = s.makefile("r", encoding="utf8", newline="\r\n")

        statusline = response.readline()
        version, status, explanation = statusline.split(" ", 2)

        response_headers = {}
        while True:
            line = response.readline()
            if line == "\r\n": break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()

            assert "transfer-encoding" not in response_headers
            assert "content-encoding" not in response_headers
        
        content = response.read()
        return content
    
    def show(self, body: str):
        in_tag = False

        for c in body:
            if c == "<":
                in_tag = True
            elif c == ">":
                in_tag = False
            elif not in_tag:
                print(c, end="")