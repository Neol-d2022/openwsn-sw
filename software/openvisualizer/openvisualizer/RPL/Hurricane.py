'''
Module which receives topology report messages .

.. moduleauthor:: Yu Yun-Shuai <yuyunshuai@gmail.com>
                  December 2015
'''
import logging
log = logging.getLogger('hurricane')
log.setLevel(logging.ERROR)
log.addHandler(logging.NullHandler())

import threading
import openvisualizer.openvisualizer_utils as u
from   datetime import datetime

from openvisualizer.eventBus import eventBusClient

#import math

class Hurricane(eventBusClient.eventBusClient):
   
    HURRICANE_PORT  = 15003
    
    def __init__(self):
                # initialize parent class
        eventBusClient.eventBusClient.__init__(
            self,
            name                  = 'Hurricane',
            registrations         =  [
               {
                    'sender'      : self.WILDCARD,
                    'signal'      : 'hurricane',
                    'callback'    : self._hurricane_notif,
                },
            ]
        )

        # local variables
        self.stateLock       = threading.Lock()
        self.hurricanedStats    = {}
        
        
    
    #======================== public ==========================================
    #Triggered by parser data as a hack 
    def _hurricane_notif(self,sender,signal,data):
        '''
        This method is invoked whenever a UDP packet is send from a mote to
        Hurricane application. This application listens at port 61618 and 
        records it.                
        '''
        #print data[0]        
        #print data[1]
        #print data[2]
        
        f = open('topology.bin', 'ab')
        newFileByteArray = bytearray( data[0] )
        f.write( newFileByteArray )
        f.close()
        
    
