# coding:utf-8

import os
from pathlib import Path
import os
import logging
import json
import requests
from functools import wraps
import time
import logging
import hashlib
from datetime import datetime, timedelta


def excel_numeric_to_date(excel_numeric_date):
    try:
        excel_epoch = datetime(1899, 12, 30)
        excel_date = excel_epoch + timedelta(days=excel_numeric_date)
        excel_date = excel_date.date()
    except:
        excel_date = excel_numeric_date
    return excel_date

def excel_date_to_numeric(dt):
    excel_epoch = datetime(1899,12,30)
    try:
        excel_numeric_date = (dt - excel_epoch).days
    except:
        excel_numeric_date = dt
    return excel_numeric_date


def timing(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time.time()
        result = f(*args, **kw)
        t = time.time()-ts
        logging.info(f'func:{f.__name__}: {t:.2f} sec')
        return result
    return wrap

def proxy(f):
    @wraps(f)
    def wrap(*args, **kw):
        set_proxy(True)
        result = f(*args, **kw)
        set_proxy(False)
        return result
    return wrap    

def set_proxy(on=True):
    if on:
        os.environ['https_proxy'] = 'http://10.110.16.62:8080' 
        os.environ['http_proxy'] = 'http://10.110.16.62:8080'
    else:
        os.environ['https_proxy'] = '' 
        os.environ['http_proxy'] = ''

def del_proxy():
    # delete proxy for solving to call api error
    if os.getenv("http_proxy") is not None:
        del os.environ['http_proxy']
    if os.getenv("https_proxy") is not None:
        del os.environ['https_proxy']

def get_project_root():
    return Path(__file__).parent.parent

#FIXME, rename to get_config_ini
def get_config_dir():
    root = get_project_root()
    config_path = os.path.join(root,'config','config.ini')
    return config_path

def get_config_dir2():
    root = get_project_root()
    config_path = os.path.join(root,'config')
    return config_path

def get_openai_api_key():
    return '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'

def get_azure_openai_api_key():
    return 'edaac76ca961490d94742cc8e7564942'
