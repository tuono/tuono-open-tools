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
Utilities for interacting with VSphere content
'''

def quantize_storage_size(size):
    '''
    Returns the storage medium size supplied in the largest appropriate units
    '''
    for item in ['bytes', 'Kib', 'Mib', 'Gib']:
        if size < 1024.0:
            return '%3.1f%s' % (size, item)
        size /= 1024.0
    return '%3.1f%s' % (size, 'Tib')


def get_all_attributes(entity):
    list = []
    for attr in dir(entity):
        if not attr.startswith('__'):
            list.append(attr)
    return list
