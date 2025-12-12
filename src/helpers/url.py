import socket
import ssl # for https, tls

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

        # Now let's send some request to server
        # First add headers
        request = "GET {} {}\r\n".format(self.path, self.__HTTP_VERSION)
        request += self.__add_header("Host", self.host)
        request += self.__add_header("Connection", "close")
        request += self.__add_header("User-Agent", "mini-browser")
        request += self.__CRLF

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
        s.close()
        return content
    
    def __add_header(self, key: str, val: str):
        '''
        It returns the header in `key: value` format
        '''
        return "{}: {}{}".format(key, val, self.__CRLF)
    
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



