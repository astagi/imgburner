imgburner
=========
Python module to write any img file on a disk.

Usage
-----
Create your Burner:

    from imgburner import Burner, ProgressListener
    burner = Burner()

Get a list of devices:

    devices = burner.list_devices()

Burn an img file:

    burner.burn(selected_device, img_path)

(OPTIONAL) define your ProgressListener:

    from imgburner import ProgressListener

    class MyProgressListener(ProgressListener):
        def on_progress_update(self, progress):
            print "Completed %d/100" % progress

        def on_error(self, error):
            print "Error!"

        def on_eject(self):
            print "Ejecting..."

        def on_completed(self):
            print "Burning process completed!"

    burner.burn(selected_device, img_path, MyProgressListener())

License
-------
This software is released under MIT License. Copyright (c) 2014 Andrea Stagi <stagi.andrea@gmail.com>