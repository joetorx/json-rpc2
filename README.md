# json-rpc2

Simple JSON-RPC 2.0 client with no dependencies other than Python's standard library.

## Requirements

Python 3.13+

## Features

* Support for JSON-RPC 1.0 and 2.0 (default)
* HTTP transport
* Basic HTTP auth
* List params
* Named params
* Notifications
* Batch support

## Usage

```
from jsonrpc2 import RpcClient

url = 'http://user:pass@localhost:8332' # omit user:pass if there is no auth
rpc = RpcClient(url)

list_params = [1, 2]
named_params = {'a': 1, 'b': 2}

# Method calling with list or named params (one or the other, not both)
resp = rpc.call('testmethod') # no params
resp = rpc.call('testmethod2', 1, 2) # list params
resp = rpc.call('testmethod2', *list_params) # list params
resp = rpc.call('testmethod2', a=1, b=2) # named params
resp = rpc.call('testmethod2', **named_params) # named params

# Batch calling
resp = rpc.batch(['testmethod', 'testmethod2'], [[], [1, 2]])
resp = rpc.batch(['testmethod2', 'testmethod2'], [{'a': 5, 'b': 3}, {'a': 2, 'b': 1}])
resp = rpc.batch(['testmethod3', 'testmethod4']) # no params

# Notification
rpc.notify('testmethod5', 'test_data')
rpc.notify('testmethod5', test_data='test_data')
rpc.batch(['testmethod5', 'testmethod5'], [['test_data'], ['test_data2']], _notify=True)

```

The response is a dictionary of the JSON response object returned from the server (even on errors). 
An exception is raised if there is an error at the HTTP level when making the call/request.

The RPC 'id' is handled internally and incremented by 1 on each request.

RPC methods can also be called directly as attributes, provided that a method list is passed when creating the client:

```
rpc = RpcClient(url, methods=['testmethod', 'testmethod2'])

resp = rpc.testmethod() # no params
resp = rpc.testmethod2(1, 2) # list params
resp = rpc.testmethod2(a=1, b=2) # named params

```

## License

Licensed under the MIT License. See the file LICENSE for details.
