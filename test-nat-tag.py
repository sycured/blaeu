#!/usr/bin/env python3

# A simple example on how to use the Blaeu package from your own
# programs.

# Here, we request only probes with the "nat" user tag and we look at their
# source address to see if it is really a legal one (RFC 1918). Some user tags
# are wrong, some are correct but the network is wrong (using non-private IP
# prefixes for the internal network).

NUM=200

import Blaeu

from netaddr import *

import sys
import time

def usage(msg=None):
    print("Usage: %s target-name-or-IP" % sys.argv[0], file=sys.stderr)
    config.usage(msg)

# RFC 1918
prefix1 = IPNetwork('10.0.0.0/8')
prefix2 = IPNetwork('172.16.0.0/12')
prefix3 = IPNetwork('192.168.0.0/16')
    
def is_private(str):
    return IPAddress(str) in prefix1 or IPAddress(str) in prefix2 or \
      IPAddress(str) in prefix3
    
config = Blaeu.Config()
(args, data) = config.parse("", []) # We don't use specific options
if len(args) != 1:
    usage("Not the good number of arguments")
    sys.exit(1)
target = args[0]
data["definitions"][0]["type"] = "ping"
data["definitions"][0]["description"] = "Test of user tag \"nat\" on %s" % target
data["definitions"][0]['af'] = 4
del data["definitions"][0]["port"]
data["definitions"][0]["packets"] = 1
data["definitions"][0]["target"] = target
if config.include is not None:
    data["probes"][0]["tags"]["include"] = copy.copy(config.include)
    data["probes"][0]["tags"]["include"].append("system-ipv4-works", "nat")
else:
    data["probes"][0]["tags"]["include"] = ["system-ipv4-works", "nat"]
data["probes"][0]["requested"] = NUM
measurement = Blaeu.Measurement(data)
rdata = measurement.results(wait=True, percentage_required=config.percentage_required)
print(("%s probes reported" % len(rdata)))
for result in rdata:
    addr = result['src_addr']
    if not is_private(addr):
        print("Probe %s has address %s which is not private" % (result['prb_id'], addr))
print(("Test #%s done at %s" % (measurement.id,
                                    time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))))

# TODO use also NAT in exclude and check the probes all have public address
