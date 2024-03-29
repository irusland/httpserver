import os


TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_DATA_DIR_NAME = 'tmp'
TEST_DATA_DIR = os.path.join(TESTS_DIR, TEST_DATA_DIR_NAME)
TEST_HANDLERS_DIR_NAME = 'handlers'
TEST_HANDLERS_DIR = os.path.join(TESTS_DIR, TEST_HANDLERS_DIR_NAME)

data_dir = TEST_DATA_DIR
handlers_dir = TEST_HANDLERS_DIR

CONFIG_PATTERN = (f'''
{{
  "_host": "0.0.0.0",
  "_port": 8000,
  "rules": {{
    "/": "{data_dir}/index.html",
    "/upload": "{data_dir}/upload.html",
    "/save": {{
      "handler": {{
        "source": "{handlers_dir}/upload.py",
        "POST": "save"
      }}
    }},
    "/show_files": {{
      "handler": {{
        "source": "{handlers_dir}/upload.py",
        "GET": "show"
      }}
    }},
    "/my_guest_book": "{data_dir}/my_guest_book.html",
    "/posts": {{
      "handler": {{
        "source": "{handlers_dir}/my_guest_book.py",
        "GET": "get_posts"
      }}
    }},
    "/post": {{
      "handler": {{
        "source": "{handlers_dir}/my_guest_book.py",
        "POST": "handle_post"
      }}
    }},
    "/c.png": {{
      "path": "{data_dir}/c.png",
      "headers": [
        [
          "Content-Type",
          "text/html"
        ],
        [
          "Content-Disposition",
          "inline;filename=custom.png"
        ]
      ]
    }},
    "/favicon.ico": "{data_dir}/pictures/favicon.ico",
    "/index.html": "{data_dir}/index.html",
    "/2.html": "{data_dir}/pages/2.html",
    "/1.2.3.txt": "{data_dir}/1.2.3.txt",
    "/page-load-errors[extras].css": {{
      "path": "pages/page-load-errors[extras].css",
      "mime": "text/css"
    }},
    "/[name].html": "{data_dir}/pages/[name].html",
    "/[name].css": "{data_dir}/pages/css/[name].css",
    "/[name].[ext]": "{data_dir}/pictures/[name].[ext]",
    "/png/[name].png": "{data_dir}/pictures/[name].png",
    "/pictures/[ext]/1": "{data_dir}/pictures/1.[ext]",
    "/[day]-[n]/[month]/[year]": "{data_dir}/dates/[year]/[month]/[day]/[n].png",
    "/[DD]/[MM]/[YY]": "{data_dir}/dates/[DD].[MM].[YY].png",
    "/mime/": {{
      "path": "{data_dir}/pictures/1.png",
      "mime": "text/txt"
    }},
    "/big": {{
      "path": "{data_dir}/pictures/chroma.jpg",
      "mime": "image/jpg"
    }},
    "/[file].[ext]": "{data_dir}/[file].[ext]"
  }},
  "error-pages": {{
    "PAGE_NOT_FOUND": "pages/PAGE_NOT_FOUND.html"
  }}
}}
    ''')


def get_config():
    return CONFIG_PATTERN
