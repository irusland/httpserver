# HTTP Server

Server which runs Hyper Text Transport Protocol

## Starting the server

```
python3 httpserver.py -c config.json --loglevel console
```

type `-h` option to specify parameters

## Running the tests

Simply run
```
python3 -m pytest tests_server.py
```

## Config settings

1) `host` Chose server host
    * use `localhost` to run locally
2) `port` Specify port for server to listen
    * default is `8000`
3) `rules` Is a map with regular language 
    * use square braces for any match (same as .*? in re)
    * type \[name\] inside braces to set named group
    * use match names in found path
        example: 
        ```
        "/[day]-[n]/[month]/[year]" : "/pictures/[year]/[month]/[day]/[n].png
        ```
        query `localhost:8000/27-me/09/2000` will display 
        a photo `/pictures/2000/09/27/me.png
        ` if exists 
        
4) `error-pages` used by Errors class

## Author

* **[Ruslan Sirazhetdinov](https://github.com/ruslansir)** - *Project creator, UrFU Student*

## Supervisor

* **[Viktor Samun](https://vk.com/victorsamun)** - *UrFU Python headquaters*