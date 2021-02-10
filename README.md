# HTTP Server

Server which runs Hyper Text Transport Protocol

Check it out at [PYPI](https://pypi.org/project/ihttpy/)

![Schema](./schema.jpg)

## Server parameters
1) `config=Configurator` Specify a configurator. Use `FluentConfigurator` for 
   type hints or `Configurator` for plain text 
1) `loglevel=LogLevel.logging` Choose a logging or console form reporting 
1) `refresh_rate=0.1` Socket connection refresh rate 
1) `cache_max_size=4e9` Max cache size

## Download

```bash
pip install ihttpy
```

## Fluent Example
```python
import ...
config = FluentConfigurator()

@config.on(Method.GET).at('/')
def index(req: Request, srv: Server)
    return Response(200, 'OK')

config._host = '0.0.0.0'
config._port = 8000
server = Server(config, loglevel=LogLevel.CONSOLE)
with server as s:
    s.run()
```


## Running the tests

```bash
python3 -m unittests discover tests/
```

## Plaintext Config settings

1) `rules` Is a map with regular language 
    * use square braces for any match (same as .*? in re)
    * type \[`name`\] inside braces to set named group
    * use match names in found path
        example: 
        ```
        "/[day]-[n]/[month]/[year]" : "/pictures/[year]/[month]/[day]/[n].png
        ```
        query `localhost:8000/27-me/09/2000` will display 
        a photo `/pictures/2000/09/27/me.png
        ` if exists
        
2) `host` Chose server host
    * use `localhost` to run locally
3) `port` Specify port for server to listen
    * default is `8000`
    
4) `error-pages` used by Errors class

## Dynamic handlers configuration

if you want more handling control:
* specify `path` field for static file response
* use `handler` object description as
    * `source` to choose handler path
    * `post` name of function to handle POST request
    * `get` name of function to handle GET request  
* specify `headers` for additional headers to be added

1) static file response `localhost:8000/my_guest_book` url 

    ```
   "/my_guest_book": "tmp/my_guest_book.html",
    ```

    router will match this url and send file `tmp/my_guest_book.html`

2) custom GET handler for `localhost:8000/posts` url 

    ```    
    "/posts": {
      "handler": {
        "source": "handlers/my_guest_book.py",
        "get": "get_posts"
      }
    }
   ```
   
   this will start loaded `source` handler search for url and call
    `get_posts` function
    
3) custom POST handler for `localhost:8000/post` url 
    
   ```
    "/post": {
      "handler": {
        "source": "handlers/my_guest_book.py",
        "post": "handle_post"
      }
    }
   ```
   
   it will call `handle_post` function from `source` found handler and process
    request in that module
    
    
    
## Dynamic handlers usage

Handlers should be added as modules with 1 or 2 functions (which are
 configured if `config.json` as it was described in 
 [here](#dynamic-handlers-configuration))
 
Its signature needs to be  
    
    def function(request: Request, server: Server) -> Response:
   
Here you can use Server and Request that is being processed 

`Request` structure:
        
* `self.method` - request method (GET/POST) 
* `self.target` - url
* `self.version` - HTTP version
* `self.headers` - headers dictionary
* `self.body` - request body

Use this properties as you need to process the request 

## Logging and debug

If you want std.out as primary output use `-l console`

If you want file as output use `-l logging`

There is a `logger.py` for server info logging and debug, configure
 LOGGER_PATH and LOG_DEBUG_PATH in `defenitions.py`   

## Author

* **[Ruslan Sirazhetdinov](https://github.com/ruslansir)** - *Project creator, UrFU Student*

## Supervisor

* **[Viktor Samun](https://vk.com/victorsamun)** - *UrFU Python headquaters*
