# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

try:
    import win32api
    from win32com.client import GetObject
    WMI = GetObject('winmgmts:')
except ImportError:
    # This file is imported on Linux hosts, but the Win32 stuff isn't needed there.
    WMI = None

BROWSER_TO_PROCESS_NAME = {
    '*googlechrome' : 'chrome.exe',
    '*iexplore' : 'iexplore.exe',
    '*iexploreproxy' : 'iexplore.exe',
    '*firefox' : 'firefox.exe',
    '*safari' : 'Safari.exe',
    '*safariproxy' : 'Safari.exe',
}
for browser, process_name in list(BROWSER_TO_PROCESS_NAME.items()):
    if browser.startswith('*'):
        BROWSER_TO_PROCESS_NAME[browser[1:]] = process_name


def get_browser_process_ids(browser):
    return get_process_ids_for_image_name(BROWSER_TO_PROCESS_NAME[browser])


# Win32 Process access rights enum as per http://msdn.microsoft.com/en-us/library/ms684880(v=vs.85).aspx
PROCESS_TERMINATE = 1

def kill_processes(process_ids):
    for pid in process_ids:
        try:
            handle = win32api.OpenProcess(PROCESS_TERMINATE, False, pid)
            win32api.TerminateProcess(handle, -1)
            win32api.CloseHandle(handle)
        except:
            # Perhaps something else killed the process?
            pass

def get_process_ids_for_image_name(image_name):
    all_processes = WMI.InstancesOf('Win32_Process')
    return [
        p.Properties_('ProcessID').Value
        for p in all_processes
        if p.Properties_('Name').Value.lower() == image_name.lower()
    ]
