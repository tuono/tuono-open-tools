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
Build a data structure representing configurations for virtual machines
on a per-cluster basis
'''

import json
import yaml

from pyVmomi import vim
from pyVmomi import vmodl
from pyVim import connect

from login import get_service_instance
from compute_spec import ComputeSpec

def main():
    si = get_service_instance()
    if not si:
        raise Exception('Authentication failed ...... please check your \
                        credentials and try again')

    content = si.RetrieveContent()
    data_dict = {}
    datacenters = content.rootFolder.childEntity
    for dc in datacenters:
        data_dict[dc.name] = {}
        clusters = dc.hostFolder.childEntity

        for cluster in clusters:
            data_dict[dc.name][cluster.name] = {}
            hosts = cluster.host

            for host in hosts:
                hostname = host.summary.config.name
                data_dict[dc.name][cluster.name][hostname] = {}
                vms = host.vm

                for vm in vms:
                    compute_spec = ComputeSpec(vm)
                    vmname = vm.summary.config.name
                    data_dict[dc.name][cluster.name][hostname][vmname] = {}
                    vm_dict = data_dict[dc.name][cluster.name][hostname][vmname]
                    vm_dict['compute'] = compute_spec.as_dictionary()

    print(yaml.dump(data_dict))

if __name__ == '__main__':
    main()
