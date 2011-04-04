#!/usr/bin/env python
"""Stop Geoserver
"""

import os, time
from subprocess import Popen, PIPE


def kill(arg1, arg2):
    """Stops a proces that contains arg1 and is filtered by arg2
    """

    # Wait until ready
    t0 = time.time()
    time_out = 30 # Wait no more than these many seconds 
    running = True

    while running and time.time()-t0 < time_out:
        p = Popen('ps aux | grep %s' % arg1, shell=True,
              stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)
              
        lines = p.stdout.readlines()

        running = False
        for line in lines:
    
            if '%s' % arg2 in line:
                running = True
        
                # Get pid
                fields = line.strip().split()

                print line
                print 'Stopping %s (process number %s)' % (arg1, fields[1])
                kill = 'kill -9 %s 2> /dev/null' % fields[1]
                os.system(kill)
   

        # Give it a little more time        
        time.sleep(1)
    else:
        print 'There are no process containing "%s" running' % arg1
    if running:
        raise Exception('Could not stop geoserver: Processes are\n %s' % str(lines))

# Kill GeoServer
kill('tomcat', 'java')
# Kill Django
kill('paster', 'project.paste')

