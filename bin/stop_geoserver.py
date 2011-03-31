"""Stop Geoserver
"""

import os, time
from subprocess import Popen, PIPE

# Wait until ready
t0 = time.time()
time_out = 30 # Wait no more than these many seconds 
running = True
while running and time.time()-t0 < time_out:
    p = Popen('ps aux | grep geoserver', shell=True,
              stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)
              
    lines = p.stdout.readlines()

    running = False
    for line in lines:
    
        if 'DSTOP.KEY=geoserver' in line:
            running = True
        
            # Get pid
            fields = line.strip().split()

            print 'Stopping Geoserver (process number %s)' % fields[1]
            kill = 'sudo kill -9 %s 2> /dev/null' % fields[1]
            os.system(kill)



    # Give it a little more time        
    time.sleep(1)

if running:
    raise Exception('Could not stop geoserver: Processes are\n %s' % str(lines))
