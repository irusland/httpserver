# HTTPClient
Client side of HTTP project

Client which runs Hyper Text Transport Protocol

## Usage
 ```
httpclient.py [-h] [-m {GET,POST}] [-F FORM] [-H HEADER] [--body BODY]
               [--user-agent USER_AGENT] [--cookie COOKIE] [-o OUTPUT]
               [--no-redirects] [--max-redirects MAX_REDIRECTS]
               [--timeout TIMEOUT]
               url
```

## Positional arguments
Url to request

## Optional arguments:
```
  -h, --help            show this help message and exit
  -m {GET,POST}, --method {GET,POST}
                        send GET or POST request
  -F FORM, --form FORM  Form-data
  -H HEADER, --header HEADER
                        Specify request header
  --body BODY           Request body
  --user-agent USER_AGENT
                        Specify UA for request
  --cookie COOKIE       Specify request cookies
  -o OUTPUT, --output OUTPUT
                        Use "--output <FILENAME>" to print save to file
  --no-redirects        No redirect parameter
  --max-redirects MAX_REDIRECTS
                        Maximum redirect count
  --timeout TIMEOUT     Set timeout for client
```

## Author

* **[Ruslan Sirazhetdinov](https://github.com/ruslansir)** - *Project creator, UrFU Student*

## Supervisor

* **[Viktor Samun](https://vk.com/victorsamun)** - *UrFU Python headquaters*