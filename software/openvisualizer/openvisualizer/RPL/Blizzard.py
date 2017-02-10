'''
Module which receives UDP ETX/Latency messages .

.. moduleauthor:: Yu Yun-Shuai <yuyunshuai@gmail.com>
                  November 2015
'''
import logging
log = logging.getLogger('blizzard')
log.setLevel(logging.ERROR)
log.addHandler(logging.NullHandler())

import threading
import openvisualizer.openvisualizer_utils as u
from   datetime import datetime

from openvisualizer.eventBus import eventBusClient

#import math

class Blizzard(eventBusClient.eventBusClient):
   
    BLIZZARD_PORT  = 15002
    
    def __init__(self):
                # initialize parent class
        eventBusClient.eventBusClient.__init__(
            self,
            name                  = 'Blizzard',
            registrations         =  [
               {
                    'sender'      : self.WILDCARD,
                    'signal'      : 'blizzard',
                    'callback'    : self._blizzard_notif,
                },
            ]
        )

        # local variables
        self.stateLock       = threading.Lock()
        self.blizzardStats    = {}
        
        
    
    #======================== public ==========================================
    #Triggered by parser data as a hack 
    def _blizzard_notif(self,sender,signal,data):
        '''
        This method is invoked whenever a UDP packet is send from a mote to
        Blizzard application. This application listens at port 61617 and 
        computes the latency of a packet. Note that this app is crosslayer
        since the mote sends the data within a UDP packet and OpenVisualizer
        (ParserData) handles that packet and reads UDP payload to compute time
        difference.
        
        At the bridge module on the DAGroot, the ASN of the DAGroot is appended
        to the serial port to be able to know what is the ASN at reception
        side.
        
        Calculate latency values are in ms[SUPERFRAMELENGTH].
        '''
        
        address       = "_".join(hex(c) for c in data[0])
        numTx      = data[1]
        numTxAck   = data[2]
        SN         = data[3]
        latency    = data[4]
        
        
        #print 'Blizzard - timeinms = ' + repr(latency)
        #print 'Blizzard - SN = ' + repr(SN)
        #print 'Blizzard - numTxAck = ' + repr(numTxAck)
        #print 'Blizzard - numTx = ' + repr(numTx)
        #print 'Blizzard - node = ' + str(address)
        
        f = open(address + '.txt', 'a')
        t = datetime.now()
        now = t.strftime("%y/%m/%d %H:%M:%S")
        f.write( now + ';' + str(SN) + ';' + str(numTx) + ';' + str(numTxAck) + ';' + str(latency) + '\n' )
        f.close()
        
        
    
    #===== formatting
    
    def _formatUDPLatencyStat(self, stats, str):
        
        output  = []
        output += ['']
        output += ['']
        output += ['============================= UDPLatency statistics =============================']
        output += ['']
        output += ['Mote address:             {0}'.format(str)]
        output += ['Min latency:              {0}ms'.format(stats.get('min'))]
        output += ['Max latency:              {0}ms'.format(stats.get('max'))]
        output += ['Packets received:         {0}'.format(stats.get('pktRcvd'))]
        output += ['Packets sent:             {0}'.format(stats.get('pktSent'))]
        output += ['Avg latency:              {0}ms'.format(stats.get('avg'))]
        output += ['Latest latency:           {0}ms'.format(stats.get('lastVal'))]
        output += ['Preferred parent:         {0}'.format(stats.get('prefParent'))]
        output += ['Sequence Number:          {0}'.format(stats.get('SN'))]
        output += ['Duplicated packets:       {0}'.format(stats.get('DUP'))]
        output += ['PLR:                      {0}%'.format(stats.get('PLR'))]
        output += ['Received:                 {0}'.format(stats.get('lastMsg'))]
        output += ['']
        output += ['']
        return '\n'.join(output)
