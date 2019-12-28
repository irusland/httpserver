# HTTP Server

Server which runs Hyper Text Transport Protocol

## Server parameters
1) `config=CONFIG_PATH` Specify config file. Will be used in Configurator
 module
1) `loglevel=LogLevel.logging` Choose logging or console form reporting 
1) `refresh_rate=0.1` Socket connection refresh rate 
1) `cache_max_size=4e9` Max cache size

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
        
    * if you want more handling control:
        * specify `path` field for static file response
        * use `handler` object description as
            * `source` to choose handler path
            * `post` name of function to handle POST request
            * `get` name of function to handle GET request  
        * specify `headers` for additional headers to be added
        
4) `error-pages` used by Errors class

## Logging and debug

If you want std.out as primary output use `-l console`

If you want file as output use `-l logging`

There is a `logger.py` for server info logging and debug, configure
 LOGGER_PATH and LOG_DEBUG_PATH in `defenitions.py`   

## Author

* **[Ruslan Sirazhetdinov](https://github.com/ruslansir)** - *Project creator, UrFU Student*

## Supervisor

* **[Viktor Samun](https://vk.com/victorsamun)** - *UrFU Python headquaters*