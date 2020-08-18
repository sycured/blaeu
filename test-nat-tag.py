#!/usr/bin/env python3

# A simple example on how to use the Blaeu package from your own
# programs.

# Here, we request only probes with the "nat" user tag and we look at their
# source address to see if it is really a legal one (RFC 1918). Some user tags
# are wrong, some are correct but the network is wrong (using non-private IP
# prefixes for the internal network).

from copy import copy
from sys import argv, exit, stderr
from time import gmtime, strftime

from netaddr import IPAddress, IPNetwork

import Blaeu

NUM = 200


def usage(msg=None):
    print(f'Usage: {argv[0]} target-name-or-IP', file=stderr)
    config.usage(msg)


# RFC 1918
prefix1 = IPNetwork('10.0.0.0/8')
prefix2 = IPNetwork('172.16.0.0/12')
prefix3 = IPNetwork('192.168.0.0/16')


def is_private(str):
    return IPAddress(str) in prefix1 or IPAddress(str) in prefix2 or \
           IPAddress(str) in prefix3


config = Blaeu.Config()
(args, data) = config.parse('', [])  # We don't use specific options
if len(args) != 1:
    usage('Not the good number of arguments')
    exit(1)
target = args[0]
data['definitions'][0]['type'] = 'ping'
data['definitions'][0][
    'description'] = f'Test of user tag "nat" on {target}'
data['definitions'][0]['af'] = 4
del data['definitions'][0]['port']
data['definitions'][0]['packets'] = 1
data['definitions'][0]['target'] = target
if config.include is not None:
    data['probes'][0]['tags']['include'] = copy(config.include)
    data['probes'][0]['tags']['include'].append('system-ipv4-works', 'nat')
else:
    data['probes'][0]['tags']['include'] = ['system-ipv4-works', 'nat']
data['probes'][0]['requested'] = NUM
measurement = Blaeu.Measurement(data)
rdata = measurement.results(wait=True,
                            percentage_required=config.percentage_required)
print(f'{len(rdata)} probes reported')
for result in rdata:
    addr = result['src_addr']
    if not is_private(addr):
        print(
            f'Probe {result["prb_id"]} has address {addr} which is not private'
        )
print(('Test #{} done at {}'.format(measurement.id,
                                    strftime("%Y-%m-%dT%H:%M:%SZ",
                                             gmtime()))))

# TODO use also NAT in exclude and check the probes all have public address
