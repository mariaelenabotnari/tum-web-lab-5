import argparse
import socket
import re
import urllib
import ssl
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

    parsed = urlparse(url)

    host = parsed.netloc
    path = parsed.path if parsed.path else "/"

    if parsed.query:
        path += "?" + parsed.query

    scheme = parsed.scheme

    if scheme == "https":
        port = 443
    else:
        port = 80

    print(f"Connecting to {host}...")

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    if scheme == "https":
        context = ssl.create_default_context()
        client_socket = context.wrap_socket(client_socket, server_hostname=host)

    client_socket.connect((host, port))

    request = f"GET {path} HTTP/1.1\r\n"
    request += f"Host: {host}\r\n"
    request += "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36\r\n"
    request += "Accept: text/html\r\n"
    request += "Accept-Encoding: identity\r\n"
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

    decoded_response = response.decode(errors="ignore")

    response_parts = decoded_response.split("\r\n\r\n", 1)

    if len(response_parts) == 2:
        body = response_parts[1]
    else:
        body = decoded_response

    return body

def build_search_url(search_terms):
    query = "+".join(search_terms)
    search_url = f"https://html.duckduckgo.com/html/?q={query}"

    return search_url

def extract_links(html_text):
    matches = re.findall(r'uddg=([^&"]+)', html_text)

    links = []

    for match in matches:
        link = urllib.parse.unquote(match)
        links.append(link)

    links = list(dict.fromkeys(links))

    return links

def perform_search(search_terms):
    search_url = build_search_url(search_terms)

    print(f"Searching for: {' '.join(search_terms)}")

    html_text = make_http_request(search_url)

    links = extract_links(html_text)

    print("\nTop results:")

    for i, link in enumerate(links[:10], start=1):
        print(f"{i}. {link}")


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
        perform_search(args.search)

    else:
        show_help()


if __name__ == "__main__":
    main()