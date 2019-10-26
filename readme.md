# HTTP Server

Server which runs Hyper Text Transport Protocol

With implemented notes app logic 

## Starting the server

```
python3 httpserver.py
```

### Allowed requests using "nc" utility

Run this in shell after server start

`nc 0.0.0.0 8000`

GET request
```
GET / HTTP/1.1
Host: 0.0.0.0:8000
Accept: text/html
```
POST request
```
POST /add?text=asdasdasd HTTP/1.1
Host: 0.0.0.0:8000
```

## Running the tests

Simply run
```
python3 -m pytest tests_server.py
```

## Author

* **[Ruslan Sirazhetdinov](https://github.com/ruslansir)** - *Project creator, UrFU Student*

## Supervisor

* **[Viktor Samun](https://vk.com/victorsamun)** - *UrFU Python headquaters*