from imgburner import Burner, ProgressListener

class MyProgressListener(ProgressListener):
    def on_progress_update(self, progress_pct):
        print "Completed %d/100" % progress_pct

    def on_error(self, error):
        print "Error!!"

    def on_eject(self):
        print "Ejecting..."

    def on_completed(self):
        print "Burning process completed!"

progress_listener = MyProgressListener()
burner = Burner()
devices = burner.list_devices()
print devices
for device in devices:
    print device['DeviceIdentifier']

img_path = "2013-09-25-wheezy-raspbian.img"
selected_device = devices[1]

burner.burn(selected_device, img_path, progress_listener)