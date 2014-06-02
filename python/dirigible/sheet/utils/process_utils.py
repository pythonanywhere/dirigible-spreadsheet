# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

from functools import wraps
import os
import pexpect
import re
import shutil
import stat
import subprocess
from tempfile import mkdtemp
import xmlrpclib

from dirigible import settings
from dirigible.sheet import calculate_server


CHROOT_REQUIRED_MOUNTS = ["/lib", "/usr/lib"]
CHROOT_DIR_PERMS = (
    stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP |
    stat.S_IROTH | stat.S_IXOTH
)


def create_chroot_jail():
    jail_dir = mkdtemp()
    os.chmod(jail_dir, CHROOT_DIR_PERMS)

    jail_etc = os.path.abspath(os.path.join(jail_dir, "etc"))
    os.mkdir(jail_etc)
    shutil.copy('/etc/resolv.conf', jail_etc)

    for required_dir in CHROOT_REQUIRED_MOUNTS:
        mount_point = "%s%s" % (jail_dir, required_dir)
        os.makedirs(mount_point)
        subprocess.call(
            ["sudo", "mount", "-r", "--bind", required_dir, mount_point]
        )

    dev_dir = os.path.abspath(os.path.join(jail_dir, "dev"))
    os.mkdir(dev_dir)
    subprocess.call(
        ["sudo", "mknod", os.path.join(dev_dir, "random"), "c", "1", "8"]
    )
    subprocess.call(
        ["sudo", "mknod", os.path.join(dev_dir, "urandom"), "c", "1", "9"]
    )

    return jail_dir


def destroy_chroot_jail(jail_dir):
    for dir in CHROOT_REQUIRED_MOUNTS:
        target_dir = os.path.join(jail_dir, dir[1:])
        subprocess.call(["sudo", "umount", "-l", target_dir])
    shutil.rmtree(jail_dir, ignore_errors=True)


def chroot_jail(func):
    '''
    Decorator to create and destroy a chroot jail around calling the decorated
    function. The chroot jail directory is passed to 'func' as an extra param.
    '''
    @wraps(func)
    def _inner(*args):
        jail_dir = create_chroot_jail()
        try:
            result = func(*(args + (jail_dir,)))
        finally:
            destroy_chroot_jail(jail_dir)
        return result

    return _inner


@chroot_jail
def chroot_calculate(
    contents_json, usercode, timeout_seconds, private_key, jail_dir
):
    server_script = os.path.abspath(
        calculate_server.__file__.replace('.pyc', '.py')
    )
    python_root = os.path.abspath(
        os.path.split(os.path.dirname(settings.__file__))[0]
    )
    try:
        process = pexpect.spawn(
            "sudo", ["python", server_script, python_root, jail_dir]
        )
        process.expect(re.compile(r'Listening on port ([0-9]+)'))
        socket = process.match.group(1)

        proxy = xmlrpclib.ServerProxy('http://localhost:%s/' % socket)
        return proxy.rpc_calculate(
            contents_json, usercode, timeout_seconds, private_key
        )
    finally:
        process.close()

