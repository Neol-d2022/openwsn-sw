#!/usr/bin/python
# Copyright (c) 2010-2013, Regents of the University of California. 
# All rights reserved. 
#  
# Released under the BSD 3-Clause license as published at the link below.
# https://openwsn.atlassian.net/wiki/display/OW/License

import logging
import threading
import copy
import random
from math import radians, cos, sin, asin, sqrt, log10

from openvisualizer.eventBus      import eventBusClient

import SimEngine

class Propagation(eventBusClient.eventBusClient):
    '''
    The propagation model of the engine.
    '''
    
    SIGNAL_WIRELESSTXSTART        = 'wirelessTxStart'
    SIGNAL_WIRELESSTXEND          = 'wirelessTxEnd'
    
    def __init__(self,simTopology):
        
        # store params
        self.engine               = SimEngine.SimEngine()
        self.simTopology          = simTopology
        
        # local variables
        self.dataLock             = threading.Lock()
        self.connections          = {}
        self.pendingTxEnd         = []
        self.errModel             = 'markov2'    # tested by YYS 2016/8/30
        #self.errModel             = ''
        self.links                = {}    # tested by YYS 2016/8/30
        self.txHistory            = {}    # tested by YYS 2016/8/30          
        self.txTotal              = 0    # tested by YYS 2016/8/31
        self.txGood               = 0    # tested by YYS 2016/8/31
        
        # logging
        self.log                  = logging.getLogger('Propagation')
        self.log.setLevel(logging.DEBUG)
        self.log.addHandler(logging.NullHandler())
        
        # initialize parents class
        eventBusClient.eventBusClient.__init__(
            self,
            name                  = 'Propagation',
            registrations         =  [
                {
                    'sender'      : self.WILDCARD,
                    'signal'      : self.SIGNAL_WIRELESSTXSTART,
                    'callback'    : self._indicateTxStart,
                },
                {
                    'sender'      : self.WILDCARD,
                    'signal'      : self.SIGNAL_WIRELESSTXEND,
                    'callback'    : self._indicateTxEnd,
                },
            ]
        )
        
        # for 2nd order Markov error model
        
    #======================== public ==========================================
    
    def createConnection(self,fromMote,toMote):
  
        
        FREQUENCY_GHz        =    2.4
        TX_POWER_dBm         =    0.0
        PISTER_HACK_LOSS     =   40.0
        SENSITIVITY_dBm      = -101.0
        GREY_AREA_dB         =   15.0
        
        with self.dataLock:
            
            if not self.simTopology:
                
                #===== Pister-hack model
                
                # retrieve position
                mhFrom            = self.engine.getMoteHandlerById(fromMote)
                (latFrom,lonFrom) = mhFrom.getLocation()
                mhTo              = self.engine.getMoteHandlerById(toMote)
                (latTo,lonTo)     = mhTo.getLocation()
    
                # compute distance
                lonFrom, latFrom, lonTo, latTo = map(radians, [lonFrom, latFrom, lonTo, latTo])
                dlon             = lonTo - lonFrom 
                dlat             = latTo - latFrom 
                a                = sin(dlat/2)**2 + cos(latFrom) * cos(latTo) * sin(dlon/2)**2
                c                = 2 * asin(sqrt(a)) 
                d_km                = 6367 * c
                
                # compute reception power (first Friis, then apply Pister-hack)
                Prx              = TX_POWER_dBm - (20*log10(d_km) + 20*log10(FREQUENCY_GHz) + 92.45)
                Prx             -= PISTER_HACK_LOSS*random.random()
               
                #turn into PDR
                if   Prx<SENSITIVITY_dBm:
                    pdr          = 0.0
                elif Prx>SENSITIVITY_dBm+GREY_AREA_dB:
                    pdr          = 1.0
                else:
                    pdr          = (Prx-SENSITIVITY_dBm)/GREY_AREA_dB

            elif self.simTopology=='linear':
                
                # linear network
                if fromMote==toMote+1:
                    pdr          = 1.0
                else:
                    pdr          = 0.0
            
            elif self.simTopology=='fully-meshed':
                
                pdr          = 1.0
            
            else:
                
                raise NotImplementedError('unsupported simTopology={0}'.format(self.simTopology))
            
            #==== create, update or delete connection
            
            if pdr:
                if fromMote not in self.connections:
                    self.connections[fromMote] = {}
                self.connections[fromMote][toMote] = pdr
                
                if toMote not in self.connections:
                    self.connections[toMote] = {}
                self.connections[toMote][fromMote] = pdr
            else:
                self.deleteConnection(toMote,fromMote)
    
    def retrieveConnections(self):
        
        retrievedConnections = []
        returnVal            = []
        with self.dataLock:
            
            for fromMote in self.connections:
                for toMote in self.connections[fromMote]:
                    if (toMote,fromMote) not in retrievedConnections:
                        returnVal += [
                            {
                                'fromMote': fromMote,
                                'toMote':   toMote,
                                'pdr':      self.connections[fromMote][toMote],
                            }
                        ]
                        retrievedConnections += [(fromMote,toMote)]
        
        return returnVal
    
    def updateConnection(self,fromMote,toMote,pdr):
        
        with self.dataLock:
            self.connections[fromMote][toMote] = pdr
            self.connections[toMote][fromMote] = pdr
    
    def deleteConnection(self,fromMote,toMote):
        
        with self.dataLock:
            
            try:
                del self.connections[fromMote][toMote]
                if not self.connections[fromMote]:
                    del self.connections[fromMote]
                
                del self.connections[toMote][fromMote]
                if not self.connections[toMote]:
                    del self.connections[toMote]
            except KeyError:
                pass # did not exist
    
    # tested by YYS 2016/8/30
    def createLink(self,fromMote,toMote,p00_0,p01_0,p10_0,p11_0):  
        
        with self.dataLock:       
           
            if fromMote not in self.links:    # dict
                self.links[fromMote] = {}
            if toMote not in self.links[fromMote]:    # dict
                self.links[fromMote][toMote] = {}
            self.links[fromMote][toMote]['p00_0'] = p00_0
            self.links[fromMote][toMote]['p01_0'] = p01_0
            self.links[fromMote][toMote]['p10_0'] = p10_0
            self.links[fromMote][toMote]['p11_0'] = p11_0
            
            if toMote not in self.links:    # dict
                self.links[toMote] = {}
            if fromMote not in self.links[toMote]:    # dict
                self.links[toMote][fromMote] = {}
            self.links[toMote][fromMote]['p00_0'] = p00_0
            self.links[toMote][fromMote]['p01_0'] = p01_0
            self.links[toMote][fromMote]['p10_0'] = p10_0
            self.links[toMote][fromMote]['p11_0'] = p11_0
            
            if fromMote not in self.txHistory:    # dict
                self.txHistory[fromMote] = {}
            if toMote not in self.txHistory[fromMote]:    # dict
                self.txHistory[fromMote][toMote] = {}
            self.txHistory[fromMote][toMote]['last2'] = 0    # last last tx is success. 0:good
            self.txHistory[fromMote][toMote]['last'] = 0     # last tx is success. 0:good
            
            if toMote not in self.txHistory:    # dict
                self.txHistory[toMote] = {}
            if fromMote not in self.txHistory[toMote]:    # dict
                self.txHistory[toMote][fromMote] = {}
            self.txHistory[toMote][fromMote]['last2'] = 0    # last last tx is success. 0:good
            self.txHistory[toMote][fromMote]['last'] = 0     # last tx is success. 0:good
                
    #======================== indication from eventBus ========================
    
    def _indicateTxStart(self,sender,signal,data):
        
        (fromMote,packet,channel) = data
        
        if fromMote in self.connections:
            for (toMote,pdr) in self.connections[fromMote].items():
                if self.errModel == 'markov2':
                    if self.txHistory[fromMote][toMote]['last2'] == 0:
                        if self.txHistory[fromMote][toMote]['last'] == 0:
                            pdr = self.links[fromMote][toMote]['p00_0']
                        else:
                            pdr = self.links[fromMote][toMote]['p01_0']
                    else:
                        if self.txHistory[fromMote][toMote]['last'] == 0:
                            pdr = self.links[fromMote][toMote]['p10_0']
                        else:
                            pdr = self.links[fromMote][toMote]['p11_0']
                            
                    self.txHistory[fromMote][toMote]['last2'] = self.txHistory[fromMote][toMote]['last']
                    self.txTotal += 1
                    if random.random()>pdr:    # tx failed                        
                        self.txHistory[fromMote][toMote]['last'] = 1    # 1:bad
                    else:
                        self.txHistory[fromMote][toMote]['last'] = 0    # 0:good
                        self.txGood += 1
                        
                        # indicate start of transmission
                        mh = self.engine.getMoteHandlerById(toMote)
                        mh.bspRadio.indicateTxStart(fromMote,packet,channel)
                        
                        # remember to signal end of transmission
                        self.pendingTxEnd += [(fromMote,toMote)]
                    print 'Good/Total: ' + str(self.txGood) + '/' + str(self.txTotal)
                                                
                else:    # Original error model, i.e. PDR only
                    if random.random()<=pdr:
                        
                        # indicate start of transmission
                        mh = self.engine.getMoteHandlerById(toMote)
                        mh.bspRadio.indicateTxStart(fromMote,packet,channel)
                        
                        # remember to signal end of transmission
                        self.pendingTxEnd += [(fromMote,toMote)]
    
    def _indicateTxEnd(self,sender,signal,data):
        
        fromMote = data
        
        if fromMote in self.connections:
            for (toMote,pdr) in self.connections[fromMote].items():
                try:
                    self.pendingTxEnd.remove((fromMote,toMote))
                except ValueError:
                    pass
                else:
                    mh = self.engine.getMoteHandlerById(toMote)
                    mh.bspRadio.indicateTxEnd(fromMote)
    
    #======================== private =========================================
    
    #======================== helpers =========================================
    
