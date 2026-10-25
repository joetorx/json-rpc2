# Copyright (c) 2026 Joel Torres
# Licensed under the MIT License. See the file LICENSE for details.

import sys
import json
import urllib.request
from urllib.parse import urlsplit
from base64 import b64encode
from http import HTTPStatus
from enum import StrEnum

class RPC_VER(StrEnum):
    V1 = '1.0'
    V2 = '2.0'

class RpcClientError(Exception):
    pass

class RpcClient:
    def __init__(self, url: str, version: str = RPC_VER.V2, methods: list = None):

        if version not in RPC_VER:
            raise RpcClientError(f'Invalid version, supported versions are: {[v.value for v in RPC_VER]}')

        self.__parse_url(url)
        self.__version = version
        self.__max_id = sys.maxsize
        self.__id = 0
        self.__notification = False
        self.__batch = False
        self.__json_object = None
        self.__methods = methods if methods else []
        self.__headers = {'Content-Type': 'application/json'}
        if self.__auth:
            b64string = b64encode(f'{self.__auth[0]}:{self.__auth[1]}'.encode())
            self.__headers['Authorization'] = f'Basic {b64string.decode()}'

        self.status = None

    def __str__(self):
        return f'<JSON-RPC {self.__version} Client>'

    def __getattr__(self, name):
        if name not in self.__methods:
            raise AttributeError(f"'{__class__.__name__}' object has no attribute '{name}'")

        def method(*args, **kwargs):
            return self.call(name, *args, **kwargs)

        return method

    def __parse_url(self, url: str) -> None:
        parsed_url = urlsplit(url)
        scheme = parsed_url.scheme
        username = parsed_url.username
        password = parsed_url.password
        hostname = parsed_url.hostname
        port = parsed_url.port
        netloc = parsed_url.netloc

        if scheme not in ['http']:
            raise RpcClientError(f'Invalid URL scheme: {scheme}')

        if not hostname:
            raise RpcClientError('No hostname in the URL')

        if not port:
            raise RpcClientError('No port in the URL')

        self.__auth = (username, password) if username and password else None
        self.__url = f'{scheme}://{netloc.split('@')[1]}' if self.__auth else f'{scheme}://{netloc.split('@')[0]}'

    def __increment_id(self) -> None:
        if self.__id == self.__max_id:
            self.__id = 1
        else:
            self.__id += 1

    def __request(self, json_object: str) -> dict | list | None:

        self.__json_object = json_object
        req = urllib.request.Request(url=self.__url, headers=self.__headers,
                                     data=json_object.encode(), method='POST')

        with urllib.request.urlopen(req) as resp:
            self.status = resp.status
            if not self.__notification:
                try:
                    response_object = json.loads(resp.read().decode())
                except Exception:
                    raise
                else:
                    return response_object

    def __build_params(self, args: tuple, kwargs: dict) -> list | dict:
        if args and kwargs:
            raise RpcClientError('Not allowed to pass both array and object for params')
        
        if self.__version == RPC_VER.V1 and kwargs:
            raise RpcClientError(f'Only array params are supported for JSON-RPC {self.__version}')
       
        if args == () and kwargs == {}:
            params = []
        elif self.__version == RPC_VER.V1:
            params = list(args)
        else:
            params = list(args) if args else kwargs

        if args and type(args[0]) == list:
            params = args[0]

        return params

    def __build_json_object(self, method: str, params: list | dict) -> dict:
        json_object = {
            'method': method,
            'params': params
        }

        if not self.__notification:
            self.__increment_id()
            json_object['id'] = str(self.__id)
        else:
            if self.__version == RPC_VER.V1:
                json_object['id'] = None

        if self.__version == RPC_VER.V2:
            json_object['jsonrpc'] = self.__version

        return json_object

    def __call(self, method: str, args: tuple, kwargs: dict) -> dict | None:
        params = self.__build_params(args, kwargs)

        json_object = self.__build_json_object(method, params)

        return self.__request(json.dumps(json_object))

    def call(self, method: str, *args, **kwargs) -> dict:

        return self.__call(method, args, kwargs)

    def notify(self, method: str, *args, **kwargs) -> None:
        self.__notification = True
        resp = self.__call(method, args, kwargs)
        self.__notification = False

        return resp

    def batch(self, method_list: list, params_list: list = None, _notify: bool = False) -> list:
        if self.__version != RPC_VER.V2:
            raise RpcClientError(f'Batch only supported for JSON-RPC {RPC_VER.V2.value}')

        if _notify:
            self.__notification = True

        if params_list is None:
            params_list = [[] for _ in range(len(method_list))]
        batch_array = []
        for method, params in zip(method_list, params_list):
            json_object = self.__build_json_object(method, params)
            batch_array.append(json_object)

        resp = self.__request(json.dumps(batch_array))

        if _notify:
            self.__notification = False

        return resp

    def get_id(self) -> int:
        return self.__id

    def get_json_object(self) -> str:
        return self.__json_object
