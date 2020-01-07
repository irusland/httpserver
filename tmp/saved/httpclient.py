import argparse
import logging
import sys
from urllib.parse import urlparse

from backend.query import Request
from backend.client_backend import Client


def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('url', help='Url to request')
    parser.add_argument('-m', '--method',
                        help='send GET or POST request',
                        choices=['GET', 'POST'],
                        default='GET')
    parser.add_argument('-F', '--form', action='append',
                        help='Form-data',
                        default=[])
    parser.add_argument('-H', '--header', action='append',
                        help='Specify request header',
                        default=[])
    parser.add_argument('--body', help='Request body'),
    parser.add_argument('--user-agent', help='Specify UA for request',
                        default='httpclient/0.4.5')
    parser.add_argument('--cookie', action='append',
                        help='Specify request cookies',
                        default=[])
    parser.add_argument('-o', '--output',
                        default=None,
                        help='Use "--output <FILENAME>" to '
                             'print save to file')
    parser.add_argument('--no-redirects', action='store_true',
                        help='No redirect parameter')
    parser.add_argument('--max-redirects', type=int, default=10,
                        help='Maximum redirect count')
    parser.add_argument('--timeout', default=1, help='Set timeout for client')
    parser.add_argument('-p', '--show-progress', action='store_true',
                        help='Use progress bar')

    args = parser.parse_args()
    url = urlparse(args.url)
    args.url = url.netloc.split(':')[0]
    args.path = url.path or '/'
    args.port = url.port
    args.header.append(f'User-Agent: {args.user_agent}')
    args.header.append(f'Connection: keep-alive')
    if args.cookie:
        args.header.append(f'Cookie: {"; ".join(args.cookie)}')
    if args.form:
        args.method = 'POST'

    return args


def main():
    args = parse()
    logging.info(args)
    try:
        with Client(timeout=args.timeout,
                    show_progress=args.show_progress) as client:
            client.connect(args.url, args.port)
            req = Request(args.method, args.path, args.url,
                          add_header=args.header, body=args.body,
                          no_redir=args.no_redirects, form=args.form,
                          max_redir=args.max_redirects)
            if args.output:
                with open(args.output, 'wb') as file:
                    client.request(req, file)
            else:
                client.request(req)

    except Exception as e:
        sys.stderr.write(str(e) + '\n')
        sys.exit(1)


if __name__ == '__main__':
    main()
