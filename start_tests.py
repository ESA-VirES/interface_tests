'''
Mini adhoc test library for all the types of requests we have
'''

import httplib
import json
import os
import fnmatch
import time
import requests
import xml.dom.minidom

from dateutil import parser



HOST = "localhost:8401"
API_URL = "/ows"

JOBURL = '''
    http://localhost:8400/ows?service=wps&request=execute&
    version=1.0.0&identifier=listJobs&RawDataOutput=job_list&json
    '''

WPSHOST = "http://localhost:8400"

passed_reqs = 0
failed_reqs = 0
dash = '=' * 90

def do_request(xml_location):
    """HTTP XML Post request"""

    global passed_reqs, failed_reqs

    request = open(xml_location, "r").read()

    webservice = httplib.HTTP(HOST)
    webservice.putrequest("POST", API_URL)
    webservice.putheader("Host", HOST)
    webservice.putheader("User-Agent", "Python post")
    webservice.putheader("Content-type", "text/xml; charset=\"UTF-8\"")
    webservice.putheader("Content-length", "%d" % len(request))
    webservice.endheaders()

    webservice.send(request)

    statuscode, statusmessage, header = webservice.getreply()
    result = webservice.getfile().read()


    if("download" in xml_location):
        if statuscode != 200:
            failed_reqs += 1
            print '{:<70s}{:^20s}'.format("Requesting %s"%xml_location, 'FAILED')

        else:
            # Check where output is generated and loop until request is finished
            #resultxml = xml.dom.minidom.parseString(result)
            # Get list of jobs
            resp = requests.get(url=JOBURL)
            jsresp = resp.json()
            latest = parser.parse("1970-05-09T14:41:41.288970+00:00")
            curr_job = None
            for process in jsresp:
                for job in xrange (len(jsresp[process])):
                    cur_job = jsresp[process][job]
                    curtime = parser.parse(cur_job["created"])
                    if latest < curtime:
                        latest = curtime
                        curr_job = cur_job["url"]

            cnt=0
            max_retry=3
            # Try to get info on job
            while cnt < max_retry:
                try:
                    response = requests.get(WPSHOST+curr_job)
                    xmlresp = xml.dom.minidom.parseString(response.content)
                    #import pdb; pdb.set_trace()
                    #wps:ProcessStarted
                    #print response
                    if xmlresp.getElementsByTagName('wps:ProcessSucceeded'):
                        passed_reqs += 1
                        print '{:<70s}{:^20s}'.format("Requesting %s"%xml_location, 'PASSED')
                        cnt = max_retry
                    elif xmlresp.getElementsByTagName('wps:ProcessFailed'):
                        failed_reqs += 1
                        print '{:<70s}{:^20s}'.format("Requesting %s"%xml_location, 'FAILED')
                        cnt = max_retry
                        # return True
                    else:
                        pass
                        #raise Exception("Job not finished")
                except requests.exceptions.RequestException as e:
                    time.sleep(5)
                    cnt += 1
                    if cnt >= max_retry:
                        raise e



    else:
        result = webservice.getfile().read()

        if statuscode != 200:
            failed_reqs += 1
            print '{:<70s}{:^20s}'.format("Requesting %s"%xml_location, 'FAILED')

        else:
            passed_reqs += 1
            print '{:<70s}{:^20s}'.format("Requesting %s"%xml_location, 'PASSED')

        #print statuscode, statusmessage, header
        #print resultxml.toprettyxml()

        # with open("output-%s" % xml_location, "w") as xmlfile:
        #     xmlfile.write(resultxml.toprettyxml())


os.chdir(".")

print "Starting tests:"
print dash


testfiles = []
for root, dirnames, filenames in os.walk('.'):
    for filename in fnmatch.filter(filenames, '*.xml'):
        testfiles.append(os.path.join(root, filename))

for file in testfiles:
    do_request(file)


print (dash)
print "PASSED requests %s/%s"%(passed_reqs,len(testfiles))
print "FAILED requests %s/%s"%(failed_reqs,len(testfiles))
