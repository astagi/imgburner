imgburner
=========
Python module to write any img file on a disk.

Usage
-----
Create your Burner:

    from imgburner import Burner
    burner = Burner()

Get a list of devices:

    devices = burner.list_devices()

You'll receive devices in this format:

    [{'Content': 'GUID_partition_scheme', 'Size': 251000193024, 'DeviceIdentifier': 'disk0', 
    'Partitions': [{'Content': 'EFI', 'DeviceIdentifier': 'disk0s1', 'Size': 209715200},
    {'Content': 'Apple_HFS', 'MountPoint': '/', 'DeviceIdentifier': 'disk0s2', 'VolumeName': 'Macintosh HD', 'Size': 250140434432},
    {'Content': 'Apple_Boot', 'VolumeName': 'Recovery HD', 'DeviceIdentifier': 'disk0s3', 'Size': 650002432}]}, 
    {'Content': 'FDisk_partition_scheme', 'Size': 15931539456, 'DeviceIdentifier': 'disk1', 
    'Partitions': [{'Content': 'Windows_FAT_32', 'MountPoint': '/Volumes/kanux-boot', 'DeviceIdentifier': 'disk1s1', 'VolumeName': 'kanux-boot', 'Size': 31457280}, 
    {'Content': 'Linux', 'DeviceIdentifier': 'disk1s2', 'Size': 1963982848}]}]

Burn an img file:

    burner.burn(selected_device, img_path)

(OPTIONAL) define your ProgressListener:

    from imgburner import ProgressListener

    class MyProgressListener(ProgressListener):
        def on_progress_update(self, progress):
            print "Completed %d/100" % progress

        def on_error(self, error):
            print "Error!"

        def on_completed(self):
            print "Burning process completed!"

    #Instance and use your burner object..

    burner.burn(selected_device, img_path, MyProgressListener())

License
-------
This software is released under MIT License. Copyright (c) 2014 Andrea Stagi <stagi.andrea@gmail.com>