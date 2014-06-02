# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

import os
import pwd
from SimpleXMLRPCServer import SimpleXMLRPCServer
import sys

# These imports are used in the tests
try:
    from dirigible.sheet.calculate import calculate_with_timeout
    from dirigible.sheet.worksheet import worksheet_from_json, worksheet_to_json
except ImportError:
    pass


def rpc_calculate(worksheet_json, usercode, timeout_seconds, private_key):
    worksheet = worksheet_from_json(worksheet_json)
    calculate_with_timeout(worksheet, usercode, timeout_seconds, private_key)
    return worksheet_to_json(worksheet)


def run(chroot_jail_path):
    server = SimpleXMLRPCServer(('localhost', 0))
    server.register_function(rpc_calculate, 'rpc_calculate')
    _, port_number = server.socket.getsockname()
    print 'Listening on port %s' % (port_number,)
    nobody_user = pwd.getpwnam("nobody").pw_uid
    os.chroot(chroot_jail_path)
    os.chdir('/')
    os.seteuid(nobody_user)
    server.handle_request()


def main():
    global calculate_with_timeout, worksheet_from_json, worksheet_to_json
    sys.path.append(sys.argv[1])
    # These imports are available inside the chroot jail
    from dirigible.sheet.calculate import calculate_with_timeout
    from dirigible.sheet.worksheet import worksheet_from_json, worksheet_to_json
    sys.path = [p for p in sys.path if 'dirigible' not in p]
    run(sys.argv[2])


if __name__ == '__main__':
    main()


