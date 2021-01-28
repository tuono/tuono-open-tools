# John Rearden 2020

'''
An abstraction to store information on the virtual disks available to a VM.

VMWare MOB:
    Data Object Type:           Virtual Hardware
    Property Path :             config.hardware
'''

import json
import yaml

from pyVmomi import vim
from utilities import quantize_storage_size

class VirtualDiskSpec():

    def __init__(self, vm):
        self.disk_dict = {}
        config = vm.config
        hardware = config.hardware
        devices = hardware.device
        for device in devices:
            if (type(device) == vim.vm.device.VirtualDisk):
                details = {}
                disk_name = device.deviceInfo.label

                size_in_bytes = device.capacityInBytes
                quantized_size = quantize_storage_size(size_in_bytes)
                size = quantized_size
                details['size'] = size

                ssd = device.backing.datastore.info.vmfs.ssd
                if ssd:
                    details['type'] = 'ssd'

                self.disk_dict[disk_name] = details

    def as_dictionary(self):
        return self.disk_dict
