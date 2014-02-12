from imgburner import Burner
import threading, time

class AutoDetectThread(threading.Thread):
    def run(self):
        burner = Burner()
        current_devices = burner.list_devices()
        while True:
            time.sleep(1)
            rescanned_devices = burner.list_devices()
            removed_devices = [x for x in current_devices if x not in rescanned_devices]
            added_devices = [x for x in rescanned_devices if x not in current_devices]
            if len(removed_devices) > 0:
                for removed_device in removed_devices:
                    print "REMOVED " + removed_device['DeviceIdentifier']
            if len(added_devices) > 0:
                for added_device in added_devices:
                    print "ADDED " + added_device['DeviceIdentifier']
            current_devices = rescanned_devices

auto_detect_thread = AutoDetectThread()
auto_detect_thread.start()