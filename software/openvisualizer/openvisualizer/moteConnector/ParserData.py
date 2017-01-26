# Copyright (c) 2010-2013, Regents of the University of California. 
# All rights reserved. 
#  
# Released under the BSD 3-Clause license as published at the link below.
# https://openwsn.atlassian.net/wiki/display/OW/License
import logging
log = logging.getLogger('ParserData')
log.setLevel(logging.ERROR)
log.addHandler(logging.NullHandler())

import struct

from pydispatch import dispatcher

from ParserException import ParserException
import Parser

class ParserData(Parser.Parser):
    
    HEADER_LENGTH  = 2
    MSPERSLOT      = 15 #ms per slot.
    
    IPHC_SAM       = 4
    IPHC_DAM       = 0
    
     
    def __init__(self):
        
        # log
        log.info("create instance")
        
        # initialize parent class
        Parser.Parser.__init__(self,self.HEADER_LENGTH)
        
        self._asn= ['asn_4',                     # B
          'asn_2_3',                   # H
          'asn_0_1',                   # H
         ]
    
        self._asn_mote= ['asn_4',                     # B
          'asn_2_3',                   # H
          'asn_0_1',                   # H
         ]
    
    #======================== public ==========================================
    
    def parseInput(self,input):
        # log
        if log.isEnabledFor(logging.DEBUG):
            log.debug("received data {0}".format(input))
        
        # ensure input not short longer than header
        self._checkLength(input)
   
        headerBytes = input[:2]
        #asn comes in the next 5bytes.  
        
        asnbytes=input[2:7]
        (self._asn) = struct.unpack('<BHH',''.join([chr(c) for c in asnbytes]))
        
        #source and destination of the message
        dest = input[7:15]
        
        #source is elided!!! so it is not there.. check that.
        source = input[15:23]
        
        if log.isEnabledFor(logging.DEBUG):
            a="".join(hex(c) for c in dest)
            log.debug("destination address of the packet is {0} ".format(a))
        
        if log.isEnabledFor(logging.DEBUG):
            a="".join(hex(c) for c in source)
            log.debug("source address (just previous hop) of the packet is {0} ".format(a))
        
        # remove asn src and dest and mote id at the beginning.
        # this is a hack for latency measurements... TODO, move latency to an app listening on the corresponding port.
        # inject end_asn into the packet as well
        input = input[23:]
        
        if log.isEnabledFor(logging.DEBUG):
            log.debug("packet without source,dest and asn {0}".format(input))
        

        # start -- trick for utyphoon
        # example packet. The last 17 bytes is the application payload.
        # [241, 130, 5, 7, 232, 122, 17, 17, 20, 21, 146, 204, 0, 0, 0, 2, 20, 21, 146, 204, 0, 0, 0, 1, 
        # 58, 153, 58, 153, 0, 25, 125, 12, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
        # port 15001==0x3a,0x99
        if (len(input) >31):
           if (input[len(input)-23]==58 and input[len(input)-22]==153):
               aux      = input[len(input)-5:]               # last 5 bytes of the packet are the ASN in the UDP packet
               diff     = self._asndiference(aux, asnbytes)  # calculate difference 
               timeinms = diff*self.MSPERSLOT                # compute time in ms
               SN       = struct.unpack('<I', bytearray(input[len(input)-5:len(input)-1]))[0]
               data_4B  = struct.unpack('<I', bytearray(input[len(input)-9:len(input)-5]))[0]
               node     = input[len(input)-17:len(input)-9] # the node address

               #print 'ASN of Mote = ' + repr(aux)
               #print 'ASN of Sink = ' + repr(asnbytes)
               #print 'Transmission time (ms) = ' + repr(timeinms)
               #print 'SN = ' + repr(SN)
               print 'data_4B = ' + repr(data_4B)
               #print 'node = ' + str(node)
               fn = 'log_data_pkt_from_' + str(node[6]*256+node[7])+ '.txt'
               f = open(fn,'a')
               f.write(repr(data_4B)+'\n')
               f.close()

               if (diff<0xFFFFFFFF):
               # notify latency manager component. only if a valid value
                  dispatcher.send(
                     sender        = 'parserData',
                     signal        = 'typhoon',
                     data          = (node,data_4B,SN,timeinms),
                  )
               else:
                   # this usually happens when the serial port framing is not correct and more than one message is parsed at the same time. this will be solved with HDLC framing.
                   print "Wrong latency computation {0} = {1} mS".format(str(node),timeinms)
                   print ",".join(hex(c) for c in input)
                   log.warning("Wrong latency computation {0} = {1} mS".format(str(node),timeinms))
                   pass
        # end -- trick for utyphoon
        
        # ublizzard
        if (len(input) >37):
            if (input[len(input)-29]==240 and input[len(input)-28]==178):         
                print "parsedata: without power, one neighbor"               
                ap_payload = input[-23:]
                dispatcher.send(
                    sender        = 'parserData',
                    signal        = 'hurricane',
                    data          = (ap_payload,0,1),
                )
            elif (input[len(input)-31]==240 and input[len(input)-30]==178):         
                print "parsedata: with power, one neighbor"               
                ap_payload = input[-25:]
                dispatcher.send(
                    sender        = 'parserData',
                    signal        = 'hurricane',
                    data          = (ap_payload,1,1),
                )
            elif (input[len(input)-41]==240 and input[len(input)-40]==178):         
                print "parsedata: without power, two neighbors"               
                ap_payload = input[-35:]
                dispatcher.send(
                    sender        = 'parserData',
                    signal        = 'hurricane',
                    data          = (ap_payload,0,2),
                )
            elif (input[len(input)-43]==240 and input[len(input)-42]==178):         
                print "parsedata: with power, two neighbors"               
                ap_payload = input[-37:]
                dispatcher.send(
                    sender        = 'parserData',
                    signal        = 'hurricane',
                    data          = (ap_payload,1,2),
                )
            elif (input[len(input)-53]==240 and input[len(input)-52]==178):         
                print "parsedata: without power, three neighbors"               
                ap_payload = input[-47:]
                dispatcher.send(
                    sender        = 'parserData',
                    signal        = 'hurricane',
                    data          = (ap_payload,0,3),
                )
            elif (input[len(input)-55]==240 and input[len(input)-54]==178):         
                print "parsedata: with power, three neighbors"               
                ap_payload = input[-49:]
                dispatcher.send(
                    sender        = 'parserData',
                    signal        = 'hurricane',
                    data          = (ap_payload,1,3),
                )

#==========================

        if (len(input) >27):
           if (input[len(input)-27]==240 and input[len(input)-26]==179):
               aux      = input[len(input)-5:]               # last 5 bytes of the packet are the ASN in the UDP packet
               diff     = self._asndiference(aux,asnbytes)   # calculate difference 
               timeinms = diff*self.MSPERSLOT                # compute time in ms
               SN       = struct.unpack('<I', bytearray(input[len(input)-5:len(input)-1]))[0]
               numTxAck = struct.unpack('<I', bytearray(input[len(input)-9:len(input)-5]))[0]
               numTx    = struct.unpack('<I', bytearray(input[len(input)-13:len(input)-9]))[0] 
               node     = input[len(input)-21:len(input)-13] # the node address

               #print 'ASN of mote = ' + repr(aux)
               #print 'ASN of NM = ' + repr(asnbytes)
               #print 'timeinms = ' + repr(timeinms)
               #print 'SN = ' + repr(SN)
               #print 'numTxAck = ' + repr(numTxAck)
               #print 'numTx = ' + repr(numTx)
               #print 'node = ' + str(node)

               if (diff<0xFFFFFFFF):
               # notify latency manager component. only if a valid value
                  dispatcher.send(
                     sender        = 'parserData',
                     signal        = 'blizzard',
                     data          = (node,numTx,numTxAck,SN,timeinms),
                  )
               else:
                   # this usually happens when the serial port framing is not correct and more than one message is parsed at the same time. this will be solved with HDLC framing.
                   print "Wrong latency computation {0} = {1} mS".format(str(node),timeinms)
                   print ",".join(hex(c) for c in input)
                   log.warning("Wrong latency computation {0} = {1} mS".format(str(node),timeinms))
                   pass
        # end - ublizzard

        # when the packet goes to internet it comes with the asn at the beginning as timestamp.
         
        # cross layer trick here. capture UDP packet from udpLatency and get ASN to compute latency.
        # then notify a latency component that will plot that information.
        # port 61001==0xee,0x49
        if (len(input) >37):
           if (input[36]==238 and input[37]==73):
            # udp port 61001 for udplatency app.
               aux      = input[len(input)-5:]               # last 5 bytes of the packet are the ASN in the UDP latency packet
               diff     = self._asndiference(aux,asnbytes)   # calculate difference 
               timeinus = diff*self.MSPERSLOT                # compute time in ms
               SN       = input[len(input)-23:len(input)-21] # SN sent by mote
               parent   = input[len(input)-21:len(input)-13] # the parent node is the first element (used to know topology)
               node     = input[len(input)-13:len(input)-5]  # the node address
               
               if (timeinus<0xFFFF):
               # notify latency manager component. only if a valid value
                  dispatcher.send(
                     sender        = 'parserData',
                     signal        = 'latency',
                     data          = (node,timeinus,parent,SN),
                  )
               else:
                   # this usually happens when the serial port framing is not correct and more than one message is parsed at the same time. this will be solved with HDLC framing.
                   print "Wrong latency computation {0} = {1} mS".format(str(node),timeinus)
                   print ",".join(hex(c) for c in input)
                   log.warning("Wrong latency computation {0} = {1} mS".format(str(node),timeinus))
                   pass
               # in case we want to send the computed time to internet..
               # computed=struct.pack('<H', timeinus)#to be appended to the pkt
               # for x in computed:
                   #input.append(x)
           else:
               # no udplatency
               # print input
               pass     
        else:
           pass      
       
        #print "UDP packet {0}".format(",".join(str(c) for c in input))
        eventType='data'
        # notify a tuple including source as one hop away nodes elide SRC address as can be inferred from MAC layer header
        return (eventType,(source,input))

 #======================== private =========================================
 
    def _asndiference(self,init,end):
      
       asninit = struct.unpack('<HHB',''.join([chr(c) for c in init]))
       asnend  = struct.unpack('<HHB',''.join([chr(c) for c in end]))
       if (asnend[2] != asninit[2]): #'byte4'
          return 0xFFFFFFFF
       else:
           pass
       
       diff = 0;
       if (asnend[1] == asninit[1]):#'bytes2and3'
          return asnend[0]-asninit[0]#'bytes0and1'
       else:
          if (asnend[1]-asninit[1]==1):##'bytes2and3'              diff  = asnend[0]#'bytes0and1'
              diff += 0xffff-asninit[0]#'bytes0and1'
              diff += 1;
          else:   
              diff = 0xFFFFFFFF
       
       return diff
