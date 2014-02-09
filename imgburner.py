import os
import sys
import subprocess
import select
import time
import signal
import math
import re
import plistlib

class ProgressListener():
    def on_progress_update(self, progress_pct):
        pass

    def on_error(self, error):
        pass

    def on_eject(self):
        pass

    def on_completed(self):
        pass

class BurnerPosix():
    #returns a list of devices
    def list_devices(self):
        p = subprocess.Popen(["diskutil", "list", "-plist"], stdout=subprocess.PIPE, 
                                       stderr=subprocess.PIPE)
        out, err = p.communicate()
        pl = plistlib.readPlistFromString(out)
        return pl['AllDisksAndPartitions']

    #fires the burn command
    def burn(self, device, img_path, progress_listener=ProgressListener()):
        #unmount selected disk and relative partitions
        for partition in device['Partitions']:
            identifier = partition['DeviceIdentifier']
            command = "diskutil unmount /dev/" + identifier
            os.system( command )
        #burn the disk
        filepath = img_path
        filesize = os.path.getsize( filepath )
        progresssize = 0
        device_identifier = device['DeviceIdentifier']
        command = 'dd bs=2m if=' + filepath + ' of=/dev/r' + device_identifier
        proc = subprocess.Popen( command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
        #inpoll = select.poll()
        #inpoll.register( proc.stdout, select.POLLIN )
        kq = select.kqueue()
        ke = select.kevent( proc.stderr )
        
        hadError = False

        while True:
            #send siginfo ctrl-t
            #hasdata = inpoll.poll(0)
            hasdata = kq.control( [ke], 1, 0.1 )

            if proc.poll() is not None:
                if proc.poll() > 0:
                    hadError = True
                break
            elif not hasdata:
                proc.send_signal( signal.SIGINFO )
                time.sleep(1)
            else:
                line = proc.stderr.readline()
                progressreg = re.compile('^(\d+) .*')
                m = progressreg.match( line )
                if m:
                    progresssize = int( m.group(1) )
                    if ( filesize > 0 ):
                        pct = float(progresssize) / float(filesize)
                        if pct > 1:
                            pct = 1
                        progress_listener.on_progress_update(int(pct*100))
                time.sleep(0.1)
        if hadError:
            progress_listener.on_error("Error during burning!")
            sys.exit(1)
        else:
            progress_listener.on_progress_update(100)
            command = "diskutil eject /dev/" + device_identifier
            progress_listener.on_eject()
            os.system( command )
            progress_listener.on_completed()

if os.name == 'posix':
    burnerClass = BurnerPosix
elif os.name == 'windows':
    raise ImportError("We're still working on Windows version")
else:
    raise ImportError("OS not supported")

class Burner(burnerClass):
    pass