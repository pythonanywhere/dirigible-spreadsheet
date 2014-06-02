# Copyright (c) 2005-2008 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

from SimpleXMLRPCServer import SimpleXMLRPCServer
from time import sleep

server = SimpleXMLRPCServer(("localhost", 8000), logRequests=False)
def do_sleep():
    sleep(0.5)
    return 0
server.register_function(do_sleep, 'do_sleep')
server.serve_forever()

