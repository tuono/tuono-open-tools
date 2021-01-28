# !/usr/bin/env python2
#
# -*- coding: utf-8 -*-
#
#  Contributors: John Rearden
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#

'''
An abstraction to contain information on the compute resources
allocated to a vm.
'''

import json
import yaml

from vdisk_spec import VirtualDiskSpec

class ComputeSpec:

    def __init__(self, vm):

        self.compute_stanza = {}
        self.vm = {}
        self.compute_stanza['vm'] = self.vm

        # Populate vm specification

        summary = vm.summary
        config = summary.config
        vm_name = vm.name

        self.vm['cores'] = config.numCpu

        memory_in_gb = config.memorySizeMB / 1024
        self.vm['memory'] = str(memory_in_gb) + 'Gb'

        self.vm['image'] = config.guestFullName

        self.vm['nic'] = 'XXXX'

        vdisk_spec = VirtualDiskSpec(vm)
        self.vm['disks'] = vdisk_spec.as_dictionary()

    def as_dictionary(self):
        return self.compute_stanza
