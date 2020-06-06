#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" A module to perform measurements on the RIPE Atlas
<http://atlas.ripe.net/> probes using the UDM (User Defined
Measurements) creation API.

Authorization key is expected in $HOME/.atlas/auth or have to be
provided in the constructor's arguments.

Stéphane Bortzmeyer <stephane+frama@bortzmeyer.org>

"""

VERSION = '1.1.6'

import os
import json
import time
import urllib.request, urllib.error, urllib.parse
import random
import copy
import sys
import getopt
import string

authfile = "%s/.atlas/auth" % os.environ['HOME']
base_url = "https://atlas.ripe.net/api/v2/measurements"

# The following parameters are currently not settable. Anyway, be
# careful when changing these, you may get inconsistent results if you
# do not wait long enough. Other warning: the time to wait depend on
# the number of the probes.
# All in seconds:
fields_delay_base = 6
fields_delay_factor = 0.2
results_delay_base = 3
results_delay_factor = 0.15
maximum_time_for_results_base = 30
maximum_time_for_results_factor = 5
# The basic problem is that there is no easy way in Atlas to know when
# it is over, either for retrieving the list of the probes, or for
# retrieving the results themselves. The only solution is to wait
# "long enough". The time to wait is not documented so the values
# above have been found mostly with trial-and-error.

class AuthFileNotFound(Exception):
    pass

class AuthFileEmpty(Exception):
    pass

class RequestSubmissionError(Exception):
    pass

class FieldsQueryError(Exception):
    pass

class MeasurementNotFound(Exception):
    pass

class MeasurementAccessError(Exception):
    pass

class ResultError(Exception):
    pass

class IncompatibleArguments(Exception):
    pass

class InternalError(Exception):
    pass

# Resut JSON file does not have the expected fields/members
class WrongAssumption(Exception):
    pass

class Config:
    def __init__(self):
        # Default values
        self.old_measurement = None
        self.measurement_id = None
        self.probes = None
        self.country = None # World-wide
        self.asn = None # All
        self.area = None # World-wide
        self.prefix = None
        self.verbose = False
        self.requested = 5 # Probes
        self.default_requested = True
        self.percentage_required = 0.9
        self.machine_readable = False
        self.measurement_id = None
        self.display_probes = False
        self.ipv4 = False
        self.private = False
        self.port = 80
        self.size = 64
        self.spread = None
        # Tags
        self.exclude = None
        self.include = None

    def usage(self, msg=None):
        if msg:
            print(msg, file=sys.stderr)
        print("""General options are:
        --verbose or -v : makes the program more talkative
        --help or -h : this message
        --displayprobes or -o : display the probes numbers (WARNING: big lists)
        --country=2LETTERSCODE or -c 2LETTERSCODE : limits the measurements to one country (default is world-wide)
        --area=AREACODE or -a AREACODE : limits the measurements to one area such as North-Central (default is world-wide)
        --asn=ASnumber or -n ASnumber : limits the measurements to one AS (default is all ASes)
        --prefix=IPprefix or -f IPprefix : limits the measurements to one IP prefix (default is all prefixes) WARNING: it must be an *exact* prefix in the global routing table
        --probes=N or -s N : selects the probes by giving explicit ID (one ID or a comma-separated list)
        --requested=N or -r N : requests N probes (default is %s)
        --percentage=X or -p X : stops the program as soon as X %% of the probes reported a result (default is %s %%)
        --measurement-ID=N or -m N : do not start a measurement, just analyze a former one
        --old_measurement MSMID or -g MSMID : uses the probes of measurement MSMID
        --include TAGS or -i TAGS : limits the measurements to probes with these tags (a comma-separated list)
        --exclude TAGS or -e TAGS : excludes from measurements the probes with these tags (a comma-separated list)
        --port=N or -t N : destination port for TCP (default is %s)
        --size=N or -z N : number of bytes in the packet (default is %s bytes)
        --ipv4 or -4 : uses IPv4 (default is IPv6, except if the parameter or option is an IP address, then it is automatically found)
        --spread or -w : spreads the tests (add a delay before the tests)
        --private : makes the measurement private
        --machinereadable or -b : machine-readable output, to be consumed by tools like grep or cut
        """ % (self.requested, int(self.percentage_required*100), self.port, self.size), file=sys.stderr)

    def parse(self, shortOptsSpecific="", longOptsSpecific=[], parseSpecific=None, usage=None):
        if usage is None:
            usage = self.usage
        try:
            optlist, args = getopt.getopt (sys.argv[1:],
                                           "4a:bc:e:f:g:hi:m:n:op:r:s:t:vw:z:" + shortOptsSpecific,
                                           ["requested=", "country=", "area=", "asn=", "prefix=", "probes=",
                                            "port=", "percentage=", "include=", "exclude=", "version",
                                            "measurement-ID=", "old_measurement=", "displayprobes", "size=",
                                            "ipv4", "private", "machinereadable", "spread=", "verbose", "help"] +
                                           longOptsSpecific)
            for option, value in optlist:
                if option == "--country" or option == "-c":
                    self.country = value
                elif option == "--area" or option == "-a":
                    self.area = value
                elif option == "--asn" or option == "-n":
                    self.asn = value
                elif option == "--prefix" or option == "-f":
                    self.prefix = value
                elif option == "--probes" or option == "-s":
                    self.probes = value # Splitting (and syntax checking...) delegated to Atlas
                elif option == "--percentage" or option == "-p":
                    self.percentage_required = float(value)
                elif option == "--requested" or option == "-r":
                    self.requested = int(value)
                    self.default_requested = False
                elif option == "--port" or option == "-t":
                    self.port = int(value)
                elif option == "--measurement-ID" or option == "-m":
                    self.measurement_id = value
                elif option == "--old_measurement" or option == "-g":
                    self.old_measurement = value
                elif option == "--verbose" or option == "-v":
                    self.verbose = True
                elif option == "--ipv4" or option == "-4":
                    self.ipv4 = True
                elif option == "--private":
                    self.private = True
                elif option == "--size" or option == "-z":
                    self.size = int(value)
                elif option == "--spread" or option == "-w":
                    self.spread = int(value)
                elif option == "--displayprobes" or option == "-o":
                    self.display_probes = True
                elif option == "--exclude" or option == "-e":
                    self.exclude = value.split(",")
                elif option == "--include" or option == "-i":
                    # TODO allows to specify stable probes https://labs.ripe.net/Members/chris_amin/new-ripe-atlas-probe-stability-system-tags
                    self.include = value.split(",")
                elif option == "--machinereadable" or option == "-b":
                    self.machine_readable = True
                elif option == "--help" or option == "-h":
                    usage()
                    sys.exit(0)
                elif option == "--version":
                    print("Blaeu version %s" % VERSION)
                    sys.exit(0)
                else:
                    parseResult = parseSpecific(self, option, value)
                    if not parseResult:
                        usage("Unknown option %s" % option)
                        sys.exit(1)
        except getopt.error as reason:
            usage(reason)
            sys.exit(1)
        if self.country is not None:
            if self.asn is not None or self.area is not None or self.prefix is not None or \
               self.probes is not None:
                usage("Specify country *or* area *or* ASn *or* prefix *or* the list of probes")
                sys.exit(1)
        elif self.area is not None:
            if self.asn is not None or self.country is not None or self.prefix is not None or \
               self.probes is not None:
                usage("Specify country *or* area *or* ASn *or* prefix *or* the list of probes")
                sys.exit(1)
        elif self.asn is not None:
            if self.area is not None or self.country is not None or self.prefix is not None or \
               self.probes is not None:
                usage("Specify country *or* area *or* ASn *or* prefix *or* the list of probes")
                sys.exit(1)
        elif self.probes is not None:
            if self.country is not None or self.area is not None or self.asn or \
               self.prefix is not None:
                usage("Specify country *or* area *or* ASn *or* prefix *or* the list of probes")
                sys.exit(1)
        elif self.prefix is not None:
            if self.country is not None or self.area is not None or self.asn or \
               self.probes is not None:
                usage("Specify country *or* area *or* ASn *or* prefix *or* the list of probes")
                sys.exit(1)
        if self.probes is not None or self.old_measurement is not None:
            if not self.default_requested:
                print("Warning: --requested=%d ignored since a list of probes was requested" % self.requested, file=sys.stderr)
        if self.old_measurement is not None:
            if self.country is not None:
                print("Warning: --country ignored since we use probes from a previous measurement", file=sys.stderr)
            if self.area is not None:
                print("Warning: --area ignored since we use probes from a previous measurement", file=sys.stderr)
            if self.prefix is not None:
                print("Warning: --prefix ignored since we use probes from a previous measurement", file=sys.stderr)
            if self.asn is not None:
                print("Warning: --asn ignored since we use probes from a previous measurement", file=sys.stderr)
            if self.probes is not None:
                print("Warning: --probes ignored since we use probes from a previous measurement", file=sys.stderr)
            # TODO include and exclude should trigger a similar warning...
        if self.probes is not None:
            self.requested = len(self.probes.split(","))
        data = { "is_oneoff": True,
                 "definitions": [
                     {"description": "", "port": self.port} ],
                 "probes": [
                     {"requested": self.requested} ] }
        if self.old_measurement is not None:
            data["probes"][0]["requested"] = 500 # Dummy value, anyway,
                                                    # but necessary to get
                                                    # all the probes
            # TODO: the huge value of "requested" makes us wait a very long time
            data["probes"][0]["type"] = "msm"
            data["probes"][0]["value"] = self.old_measurement
            data["definitions"][0]["description"] += (" from probes of measurement #%s" % self.old_measurement)
        else:
            if self.probes is not None:
                data["probes"][0]["type"] = "probes"
                data["probes"][0]["value"] = self.probes
            else:
                if self.country is not None:
                    data["probes"][0]["type"] = "country"
                    data["probes"][0]["value"] = self.country
                    data["definitions"][0]["description"] += (" from %s" % self.country)
                elif self.area is not None:
                    data["probes"][0]["type"] = "area"
                    data["probes"][0]["value"] = self.area
                    data["definitions"][0]["description"] += (" from %s" % self.area)
                elif self.asn is not None:
                    data["probes"][0]["type"] = "asn"
                    data["probes"][0]["value"] = self.asn
                    data["definitions"][0]["description"] += (" from AS #%s" % self.asn)
                elif self.prefix is not None:
                    data["probes"][0]["type"] = "prefix"
                    data["probes"][0]["value"] = self.prefix
                    data["definitions"][0]["description"] += (" from prefix %s" % self.prefix)
                else:
                    data["probes"][0]["type"] = "area"
                    data["probes"][0]["value"] = "WW"
        if self.ipv4:
            data["definitions"][0]['af'] = 4
        else:
            data["definitions"][0]['af'] = 6 
        if self.private:
            data["definitions"][0]['is_public'] = False
        if self.size is not None:
            data["definitions"][0]['size'] = self.size    
        if self.spread is not None:
            data["definitions"][0]['spread'] = self.spread
        data["probes"][0]["tags"] = {}
        if self.include is not None:
            data["probes"][0]["tags"]["include"] = copy.copy(self.include)
        else:
            data["probes"][0]["tags"]["include"] = []
        if self.ipv4:
            data["probes"][0]["tags"]["include"].append("system-ipv4-works") # Some probes cannot do ICMP outgoing (firewall?)
        else:
            data["probes"][0]["tags"]["include"].append("system-ipv6-works")
        if self.exclude is not None:
            data["probes"][0]["tags"]["exclude"] = copy.copy(self.exclude)
        if self.verbose:
            print("Blaeu version %s" % VERSION)
        return args, data
    
class JsonRequest(urllib.request.Request):
    def __init__(self, url):
        urllib.request.Request.__init__(self, url)
        self.url = url
        self.add_header("Content-Type", "application/json")
        self.add_header("Accept", "application/json")
        self.add_header("User-Agent", "RIPEAtlas.py")
    def __str__(self):
        return self.url

class Measurement():
    """ An Atlas measurement, identified by its ID (such as #1010569) in the field "id" """

    def __init__(self, data, wait=True, sleep_notification=None, key=None, id=None):
        """
        Creates a measurement."data" must be a dictionary (*not* a JSON string) having the members
        requested by the Atlas documentation. "wait" should be set to False for periodic (not
        oneoff) measurements. "sleep_notification" is a lambda taking one parameter, the
        sleep delay: when the module has to sleep, it calls this lambda, allowing you to be informed of
        the delay. "key" is the API key. If None, it will be read in the configuration file.

        If "data" is None and id is not, a dummy measurement will be created, mapped to
         the existing measurement having this ID.
        """

        if data is None and id is None:
            raise RequestSubmissionError("No data and no measurement ID")
        
        # TODO: when creating a dummy measurement, a key may not be necessary if the measurement is public
        if not key:
            if not os.path.exists(authfile):
                raise AuthFileNotFound("Authentication file %s not found" % authfile)
            auth = open(authfile)
            key = auth.readline()
            if key is None or key == "":
                raise AuthFileEmpty("Authentication file %s empty or missing a end-of-line at the end" % authfile)
            key = key.rstrip('\n')
            auth.close()

        self.url = base_url + "/?key=%s" % key
        self.url_probes = base_url + "/%s/?fields=probes,status" + "&key=%s" % key
        self.url_status = base_url + "/%s/?fields=status" + "&key=%s" % key 
        self.url_results = base_url + "/%s/results/" + "?key=%s" % key
        self.url_all = base_url + "/%s/" + "?key=%s" % key
        self.url_latest = base_url + "-latest/%s/?versions=%s"

        self.status = None
        
        if data is not None:
            self.json_data = json.dumps(data).encode('utf-8')
            self.notification = sleep_notification
            request = JsonRequest(self.url)
            try:
                # Start the measurement
                conn = urllib.request.urlopen(request, self.json_data)
                # Now, parse the answer
                results = json.loads(conn.read().decode('utf-8'))
                self.id = results["measurements"][0]
                conn.close()
            except urllib.error.HTTPError as e:
                raise RequestSubmissionError("Status %s, reason \"%s : %s\"" % \
                                             (e.code, e.reason, e.read()))
            except urllib.error.URLError as e:
                raise RequestSubmissionError("Reason \"%s\"" % \
                                             (e.reason))


            self.gen = random.Random()
            self.time = time.gmtime()
            if not wait:
                return
            # Find out how many probes were actually allocated to this measurement
            enough = False
            left = 30 # Maximum number of tests
            requested = data["probes"][0]["requested"] 
            fields_delay = fields_delay_base + (requested * fields_delay_factor)
            while not enough:
                # Let's be patient
                if self.notification is not None:
                    self.notification(fields_delay)
                time.sleep(fields_delay)
                fields_delay *= 2
                try:
                    request = JsonRequest((self.url_probes % self.id) + \
                                          ("&defeatcaching=dc%s" % self.gen.randint(1,10000))) # A random
                                # component is necesary to defeat caching (even Cache-Control sems ignored)
                    conn = urllib.request.urlopen(request)
                    # Now, parse the answer
                    meta = json.loads(conn.read().decode('utf-8'))
                    self.status = meta["status"]["name"] 
                    if meta["status"]["name"] == "Specified" or \
                           meta["status"]["name"] == "Scheduled":
                        # Not done, loop
                        left -= 1
                        if left <= 0:
                            raise FieldsQueryError("Maximum number of status queries reached")
                    elif meta["status"]["name"] == "Ongoing":
                        enough = True
                        self.num_probes = len(meta["probes"])
                    else:
                        raise InternalError("Internal error in #%s, unexpected status when querying the measurement fields: \"%s\"" % (self.id, meta["status"]))
                    conn.close()
                except urllib.error.URLError as e:
                    raise FieldsQueryError("%s" % e.reason)
        else:
            self.id = id
            self.notification = None
            try:
                conn = urllib.request.urlopen(JsonRequest(self.url_status % self.id))
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    raise MeasurementNotFound
                else:
                    raise MeasurementAccessError("HTTP %s, %s %s" % (e.code, e.reason, e.read()))
            except urllib.error.URLError as e:
                raise MeasurementAccessError("Reason \"%s\"" % \
                                             (e.reason))
            result_status = json.loads(conn.read().decode('utf-8'))
            status = result_status["status"]["name"]
            self.status = status
            if status != "Ongoing" and status != "Stopped":
                raise MeasurementAccessError("Invalid status \"%s\"" % status)
            try:
                conn = urllib.request.urlopen(JsonRequest(self.url_probes % self.id))
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    raise MeasurementNotFound
                else:
                    raise MeasurementAccessError("%s %s" % (e.reason, e.read()))
            except urllib.error.URLError as e:
                raise MeasurementAccessError("Reason \"%s\"" % \
                                             (e.reason))
            result_status = json.loads(conn.read().decode('utf-8')) 
            self.num_probes = len(result_status["probes"])
        try:
                conn = urllib.request.urlopen(JsonRequest(self.url_all % self.id))
        except urllib.error.HTTPError as e:
                if e.code == 404:
                        raise MeasurementNotFound
                else:
                        raise MeasurementAccessError("%s %s" % (e.reason, e.read()))
        except urllib.error.URLError as e:
                raise MeasurementAccessError("Reason \"%s\"" % \
                                             (e.reason))
        result_status = json.loads(conn.read().decode('utf-8'))
        self.time = time.gmtime(result_status["start_time"])
        self.description = result_status["description"]
        self.interval = result_status["interval"]
            
    def results(self, wait=True, percentage_required=0.9, latest=None):
        """Retrieves the result. "wait" indicates if you are willing to wait until
        the measurement is over (otherwise, you'll get partial
        results). "percentage_required" is meaningful only when you wait
        and it indicates the percentage of the allocated probes that
        have to report before the function returns (warning: the
        measurement may stop even if not enough probes reported so you
        always have to check the actual number of reporting probes in
        the result). "latest" indicates that you want to retrieve only
        the last N results (by default, you get all the results).
        """
        if latest is not None:
            wait = False
        if latest is None:
            request = JsonRequest(self.url_results % self.id)
        else:
            request = JsonRequest(self.url_latest% (self.id, latest))
        if wait:
            enough = False
            attempts = 0
            results_delay = results_delay_base + (self.num_probes * results_delay_factor)
            maximum_time_for_results = maximum_time_for_results_base + \
                                       (self.num_probes * maximum_time_for_results_factor)
            start = time.time()
            elapsed = 0
            result_data = None
            while not enough and elapsed < maximum_time_for_results:
                if self.notification is not None:
                    self.notification(results_delay)
                time.sleep(results_delay) 
                results_delay *= 2
                attempts += 1
                elapsed = time.time() - start
                try:
                    conn = urllib.request.urlopen(request)
                    result_data = json.loads(conn.read().decode('utf-8'))
                    num_results = len(result_data)
                    if num_results >= self.num_probes*percentage_required:
                        # Requesting a strict equality may be too
                        # strict: if an allocated probe does not
                        # respond, we will have to wait for the stop
                        # of the measurement (many minutes). Anyway,
                        # there is also the problem that a probe may
                        # have sent only a part of its measurements.
                        enough = True
                    else:
                        conn = urllib.request.urlopen(JsonRequest(self.url_status % self.id))
                        result_status = json.loads(conn.read().decode('utf-8')) 
                        status = result_status["status"]["name"]
                        if status == "Ongoing":
                            # Wait a bit more
                            pass
                        elif status == "Stopped":
                            enough = True # Even if not enough probes
                        else:
                            raise InternalError("Unexpected status when retrieving the measurement: \"%s\"" % \
                                   result_data["status"])
                    conn.close()
                except urllib.error.HTTPError as e:
                    if e.code != 404: # Yes, we may have no result file at
                        # all for some time
                        raise ResultError(str(e.code) + " " + e.reason + " " + e.read())
                except urllib.error.URLError as e:
                    raise ResultError("Reason \"%s\"" % \
                                             (e.reason))
            if result_data is None:
                raise ResultError("No results retrieved")
        else:
            try:
                conn = urllib.request.urlopen(request)
                result_data = json.loads(conn.read().decode('utf-8'))
            except urllib.error.URLError as e:
                raise ResultError(e.reason)
        return result_data
