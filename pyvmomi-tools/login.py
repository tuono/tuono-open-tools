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
Tools to authenticate and return a pyVmomi ServiceInstance
'''

import argparse
import atexit

from pyVmomi import vim
from pyVmomi import vmodl
from pyVim import connect

def get_args():
    parser = argparse.ArgumentParser(
        description='Process arguments for querying the vcenter'
    )

    parser.add_argument('-s', '--host',
                        required=True, action='store',
                        help='Remote host to connect to')
    parser.add_argument('-o', '--port',
                        type=int, default=443,
                        action='store', help='Port to connect to')
    parser.add_argument('-u', '--user',
                        required=True, action='store',
                        help='User name to use when connecting')
    parser.add_argument('-p', '--password',
                        required=True, action='store',
                        help='Password to use when connecting')
    parser.add_argument('-n', '--nossl',
                        required=False, action='store_true',
                        help='Flag to set only if ssl should not be used')
    args = parser.parse_args()
    return args


def get_service_instance():
    args = get_args()
    try:
        if (args.nossl):
            service_instance = connect.SmartConnectNoSSL(host=args.host,
                                                        user=args.user,
                                                        pwd=args.password,
                                                        port=int(args.port))
        else:
            service_instance = connect.SmartConnect(host=args.host,
                                                    user=args.user,
                                                    pwd=args.password,
                                                    port=int(args.port))
        if not service_instance:
            print('Problem connecting - check host/username/password')
            return -1

        atexit.register(connect.Disconnect, service_instance)

    except vmodl.MethodFault as error:
        print ('Caught vmodl fault : ' + error.msg)
        return None

    return service_instance
