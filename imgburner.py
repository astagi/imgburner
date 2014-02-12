import os
import sys
import subprocess
import select
import time
import signal
import math
import re
import shlex
import platform

class ProgressListener():
    def on_progress_update(self, progress_pct):
        pass

    def on_error(self, error):
        pass

    def on_eject(self):
        pass

    def on_completed(self):
        pass

class Utilities():
    @classmethod
    def human_format_to_bytes(cls, human_format):
        progressreg = re.compile('^(\d+)\s*(..)')
        m = progressreg.match( human_format )
        if m:
            value = int( m.group(1) )
            unit = m.group(2).lower()
            mul = 0
            if unit == 'kb':
                mul = 1
            elif unit == 'mb':
                mul = 2
            elif unit == 'gb':
                mul = 3
            elif unit == 'tb':
                mul = 4
        return value * (1000**mul)

current_os = platform.system()

if current_os == 'Darwin':

    import plistlib
    class Burner():
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
            else:
                progress_listener.on_progress_update(100)
                command = "diskutil eject /dev/" + device_identifier
                progress_listener.on_eject()
                os.system( command )
                progress_listener.on_completed()

elif current_os == 'Linux':

    class Burner():
        #returns a list of devices
        def list_devices(self):
            proc = subprocess.Popen(shlex.split("lsblk -o name,mountpoint,label,size,type --raw"),
                            stdout = subprocess.PIPE, stderr = subprocess.PIPE)
            fdisk_output, fdisk_error = proc.communicate()
            current_disk = -1
            disks = []
            try:
                for line in fdisk_output.split("\n"):
                    if line and line.startswith("NAME"): continue
                    parts = line.split(" ")
                    disk = {}
                    disk['DeviceIdentifier'] = parts[0]
                    disk['MountPoint'] = parts[1]
                    disk['VolumeName'] = parts[2]
                    disk['Size'] = parts[3]
                    if parts[4] == "disk":
                        current_disk += 1
                        disk['Partitions'] = []
                        disks.append(disk)
                    else:
                        disks[current_disk]['Partitions'].append(disk)
            except IndexError:
                pass
            return disks

        #fires the burn command
        def burn(self, device, img_path, progress_listener=ProgressListener()):
            #unmount selected disk and relative partitions
            for partition in device['Partitions']:
                identifier = partition['DeviceIdentifier']
                command = "umount /dev/" + identifier
                os.system( command )
            #burn the disk
            filepath = img_path
            filesize = os.path.getsize( filepath )
            progresssize = 0
            device_identifier = device['DeviceIdentifier']
            command = 'dd if=' + filepath + ' of=/dev/' + device_identifier
            dd = subprocess.Popen(shlex.split(command), stderr=subprocess.PIPE )

            hadError = False

            while dd.poll() is None:
                time.sleep(.3)
                dd.send_signal(signal.SIGUSR1)
                while 1:
                    line = dd.stderr.readline()
                    progressreg = re.compile('^(\d+) .*')
                    m = progressreg.match( line )
                    if m:
                        progresssize = int( m.group(1) )
                        if ( filesize > 0 ):
                            pct = float(progresssize) / float(filesize)
                            if pct > 1:
                                pct = 1
                            progress_listener.on_progress_update(int(pct*100))
                        break
                    time.sleep(0.1)

            print dd.stderr.read(),
            if hadError:
                progress_listener.on_error("Error during burning!")
            else:
                progress_listener.on_progress_update(100)
                """command = "diskutil eject /dev/" + device_identifier
                progress_listener.on_eject()
                os.system( command )"""
                progress_listener.on_completed()

elif current_os == 'Windows':
    from xml.dom.minidom import parseString
    class Burner():
        #returns a list of devices
        def list_devices(self):
            
            def get_xml_value(property, default_value=''):
                if not property:
                    return default_value
                if not property.firstChild:
                    return default_value
                if not property.firstChild.firstChild:
                    return default_value
                return property.firstChild.firstChild.nodeValue

            proc = subprocess.Popen(shlex.split("wmic logicaldisk get deviceid,caption,volumename,size /format:rawxml.xsl"),
                            stdout = subprocess.PIPE, stderr = subprocess.PIPE)
            out, err = proc.communicate()
            dom = parseString(out)
            disks = []
            for instance in dom.getElementsByTagName('INSTANCE'):
                properties = instance.getElementsByTagName("PROPERTY")
                disk = {}
                disk['MountPoint'] = get_xml_value(properties[0])
                disk['DeviceIdentifier'] = get_xml_value(properties[1])
                disk['Size'] = long(get_xml_value(properties[2], 0))
                disk['VolumeName'] = get_xml_value(properties[3])
                disks.append(disk)
            return disks

        #fires the burn command
        def burn(self, device, img_path, progress_listener=ProgressListener()):
            filepath = img_path
            filesize = os.path.getsize( filepath )
            progresssize = 0
            device_identifier = device['DeviceIdentifier']
            command = "bin/flashnul.exe " + device_identifier + " -L " + filepath + " -P -k"
            p = subprocess.Popen(shlex.split(command),stderr=subprocess.PIPE,stdout=subprocess.PIPE, universal_newlines=True)

            for line in iter(p.stderr.readline, ""):
                progressreg = re.compile('^.* \((\d+ ..)\), .*')
                m = progressreg.match( line )
                if m:
                    progresssize = m.group(1)
                    progresssize = Utilities.human_format_to_bytes(progresssize)
                    if ( filesize > 0 ):
                        pct = float(progresssize) / float(filesize)
                        if pct > 1:
                            pct = 1
                        progress_listener.on_progress_update(int(pct*100))
                sys.stderr.flush()

            progress_listener.on_progress_update(100)
            progress_listener.on_eject()
            progress_listener.on_completed()

else:
    raise ImportError("OS not supported")