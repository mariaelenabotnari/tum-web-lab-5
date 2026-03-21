import argparse
import socket
import re
import urllib
import ssl
import os
import hashlib
import json
from urllib.parse import urlparse
from bs4 import BeautifulSoup


SEARCH_RESULTS_FILE = "last_search_results.txt"
CACHE_DIR = "cache"


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


def make_http_request(url, redirect_count=0):
    ensure_cache_dir()

    cached_data = load_from_cache(url)
    if cached_data is not None:
        print(f"Loading from cache: {url}")
        return cached_data

    if redirect_count > 5:
        print("Too many redirects.")
        return "", ""

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

    request = f"GET {path} HTTP/1.0\r\n"
    request += f"Host: {host}\r\n"
    request += "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36\r\n"
    request += "Accept: text/html, application/json\r\n"
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
        headers = response_parts[0]
        body = response_parts[1]
    else:
        headers = decoded_response
        body = ""

    if "Transfer-Encoding: chunked" in headers:
        # Removes any line that is purely hexadecimal
        body = re.sub(r'^[0-9a-fA-F]+\r\n', '', body, flags=re.MULTILINE)

    status_line = headers.split("\r\n")[0]

    if "301" in status_line or "302" in status_line:
        location_match = re.search(r"Location: (.+)", headers)
        if location_match:
            redirect_url = location_match.group(1).strip()
            print(f"Redirecting to: {redirect_url}")
            return make_http_request(redirect_url, redirect_count + 1)

    full_content = headers + "\r\n\r\n" + body
    save_to_cache(url, full_content)

    return headers, body


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

    # Unpack both headers and body
    _, html_text = make_http_request(search_url)

    links = extract_links(html_text)
    save_search_results(links)
    print("\nTop results:")
    for i, link in enumerate(links[:10], start=1):
        print(f"{i}. {link}")


def save_search_results(links):
    with open(SEARCH_RESULTS_FILE, "w", encoding="utf-8") as file:
        for link in links:
            file.write(link + "\n")


def load_search_result_by_index(index):
    try:
        with open(SEARCH_RESULTS_FILE, "r", encoding="utf-8") as file:
            links = [line.strip() for line in file.readlines() if line.strip()]

        if 1 <= index <= len(links):
            return links[index - 1]
        else:
            return None

    except FileNotFoundError:
        return None


def ensure_cache_dir():
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)


def get_cache_filename(url):
    url_hash = hashlib.md5(url.encode()).hexdigest()
    return os.path.join(CACHE_DIR, f"{url_hash}.txt")


def load_from_cache(url):
    cache_file = get_cache_filename(url)
    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8", newline='') as file:
            data = file.read()
            parts = re.split(r'\r?\n\r?\n', data, maxsplit=1)
            if len(parts) == 2:
                return parts[0], parts[1]
    return None


def save_to_cache(url, content):
    cache_file = get_cache_filename(url)

    with open(cache_file, "w", encoding="utf-8", newline='') as file:
        file.write(content)


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-u", "--url", type=str)
    parser.add_argument("-s", "--search", nargs="+")
    parser.add_argument("-h", "--help", action="store_true")
    args = parser.parse_args()

    if args.help:
        show_help()
    elif args.url:
        url_to_open = args.url
        if args.url.isdigit():
            selected_index = int(args.url)
            saved_link = load_search_result_by_index(selected_index)
            if saved_link is None:
                print("Invalid result number.")
                return
            url_to_open = saved_link
            print(f"Opening saved result #{selected_index}: {url_to_open}")

        headers, raw_body = make_http_request(url_to_open)

        if "application/json" in headers.lower():
            try:
                json_data = json.loads(raw_body)
                print("\nJSON Content Detected\n")
                print(json.dumps(json_data, indent=4))
            except json.JSONDecodeError:
                print("Error: Could not parse JSON.")
        else:
            soup = BeautifulSoup(raw_body, "html.parser")
            for script_or_style in soup(["script", "style"]):
                script_or_style.decompose()
            print(soup.get_text(separator="\n", strip=True))

    elif args.search:
        perform_search(args.search)
    else:
        show_help()


if __name__ == "__main__":
    main()