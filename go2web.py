import argparse
import socket
from urllib.parse import urlparse


def show_help():
    print("go2web -u <URL>         make an HTTP request to the specified URL")
    print("go2web -s <search-term> search the term using a search engine")
    print("go2web -h               show this help")

def parse_url(url):
    parsed_url = urlparse(url)

    host = parsed_url.netloc

    if parsed_url.path:
        path = parsed_url.path
    else:
        path = "/"

    return host, path

def make_http_request(url):
    host, path = parse_url(url)

    port = 80

    print(f"Connecting to {host}...")

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    request = f"GET {path} HTTP/1.1\r\n"
    request += f"Host: {host}\r\n"
    request += "Connection: close\r\n"
    request += "\r\n"

    client_socket.send(request.encode())

    response = b""

    while True:
        data = client_socket.recv(4096)
        if not data:
            break
        response += data

    client_socket.close()

    print(response.decode(errors="ignore"))


def main():
    parser = argparse.ArgumentParser(add_help=False)

    parser.add_argument("-u", "--url", type=str)
    parser.add_argument("-s", "--search", nargs="+")
    parser.add_argument("-h", "--help", action="store_true")

    args = parser.parse_args()

    if args.help:
        show_help()

    elif args.url:
        make_http_request(args.url)

    elif args.search:
        search_term = " ".join(args.search)
        print(f"Search not implemented yet: {search_term}")

    else:
        show_help()


if __name__ == "__main__":
    main()