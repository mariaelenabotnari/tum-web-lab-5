import argparse
import socket
import re
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

    decoded_response = response.decode(errors="ignore")

    parts = decoded_response.split("\r\n\r\n", 1)

    if len(parts) == 2:
        body = parts[1]
    else:
        body = decoded_response

    body = body.replace("</p>", "\n")
    body = body.replace("</h1>", "\n")
    body = body.replace("</div>", "\n")
    body = body.replace("<br>", "\n")

    body = re.sub(r"<style.*?>.*?</style>", "", body, flags=re.DOTALL)
    body = re.sub(r"<script.*?>.*?</script>", "", body, flags=re.DOTALL)
    body = re.sub(r"\b[0-9a-fA-F]+\b\r?\n", "", body)

    clean_text = re.sub(r"<[^>]+>", "", body)
    clean_text = clean_text.strip()

    print(clean_text)

def build_search_url(search_terms):
    query = "+".join(search_terms)
    search_url = f"http://duckduckgo.com/html/?q={query}"

    return search_url


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
        search_url = build_search_url(args.search)
        print("Search request prepared")
        print(f"Search URL: {search_url}")

    else:
        show_help()


if __name__ == "__main__":
    main()