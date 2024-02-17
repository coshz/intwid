import logging
import os
import requests


def create_logger(
    log_name, 
    log_level=logging.DEBUG,
    cmd_level=logging.INFO,
    formatter=logging.Formatter("%(asctime)s - %(levelname)s: %(message)s")
):
    fh = logging.FileHandler(f"{log_name}.log")
    fh.setLevel(log_level)
    fh.setFormatter(formatter)
    sh = logging.StreamHandler()
    sh.setLevel(cmd_level)
    sh.setFormatter(formatter)

    logger = logging.Logger(log_name)
    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger


class DownloadHelper:

    # we define `cookie` as a class attribute (and `self.download_worker` as a staticmethod) 
    # to evade pickling logger.
    cookie_     = ''

    def __init__(self, cookie=None):
        self.init_cookie(cookie_file=cookie)

    @classmethod
    def get_header(cls):
        return { 
            "User-Agent":   'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36',
            "Referer":      'https://weibo.com/',
            "Cookie":       cls.cookie_
        }

    @classmethod
    def init_cookie(cls, cookie_file):
        if cookie_file:
            if not os.path.exists(cookie_file):
                print(f"Error: cookie file is specified but it is not found.")
                exit()
            with open(cookie_file,'r') as f:
                print(f"Info: cookie is loaded from file `{cookie_file}`")
                cls.cookie_ = f.read().strip()
    
    @classmethod
    def worker_fn(cls, url, path):
        if os.path.exists(path): return None, None
        try:
            r = requests.get(url, headers=cls.get_header(), timeout=(5,10), stream=True)
            r.raise_for_status()
        except Exception as e:
            return e, (url, path)
        else:
            with open(path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=4096):
                    f.write(chunk)
            return None, None

# def retry_helper(tries=2, exceptions=Exception):
#     from functools import wraps
#     import random
#     import time
#     def decorator(f):
#         @wraps(f)
#         def wrapper(*args, **kwargs):
#             for n in range(tries):
#                 try:
#                     return f(*args, **kwargs)
#                 except exceptions as e:
#                     print(f"exception {e}, retrying {n+1} / {tries} ...")
#                     time.sleep(random.uniform(30,60))
#             else:
#                 return f(*args, **kwargs)
#         return wrapper
#     return decorator