
import re
import uuid

from frappy.core import BUSY, IDLE, Command, Drivable, HasIO, IntRange, \
    Parameter, Readable, StructOf
from frappy.datatypes import ArrayOf, EnumType, FloatRange, StatusType, \
    StringType
from frappy.errors import ImpossibleError, IsBusyError
from frappy.lib.enum import Enum
from frappy.modules import Attached

nsamples = 12

EMPTY_SLOT = ""


class Magazin:

    
    def __init__(self,nSamples):
        self.samples = [""] * nSamples
          
    def get_freeSlot(self):
        return self.get_index("")

        
    def insertSample(self,sample_id:str):
        
        slot = self.get_freeSlot()
        
        if slot != None: 
            raise Exception("Magazine is already full")
        
           
        self.samples[slot] = sample_id
                   
            
    def removeSample(self,sample_id):
        self.samples.remove(sample_id)

                    
    def get_index(self,sample_id):
        try:
            return self.samples.index(sample_id)
        except ValueError:
            return None 
        

    
    def get_sample(self,slot):
        return self.samples[slot]      
    
    def updateSample(self,slot,sample_id):
        if self.samples[slot] != EMPTY_SLOT:
            raise Exception("no sample present at slot: "+ str(slot))
        else: 
            self.samples[slot] = sample_id
            


            



class Storage(HasIO,Readable):
    
    Status = Enum(
        Drivable.Status,
        DISABLED = StatusType.DISABLED,
        PREPARING = StatusType.PREPARING,
        LOADING=303,
        UNLOADING = 304,
        PAUSED = 305,
        STOPPED = 402,
        LOCAL_CONTROL = 403,
        LOCKED = 404 
        )  #: status codes

    status = Parameter(datatype=StatusType(Status))  # override Readable.status 
    
    
    a_hardware = Attached(mandatory = True)
    a_sample   = Attached(mandatory = True)
    
    value = Parameter("Sample objects in storage",
                    datatype=ArrayOf(StringType(maxchars=100)),
                    readonly = True)
    
    
    
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.mag = Magazin(nsamples)

        
    def read_status(self):
        robo_stat = self.a_hardware.status
        
        
        
        # Robot Arm is Busy        
        if robo_stat[0] == BUSY:
            if re.match(r'in\d+\.urp',self.a_hardware.loaded_prog):
                return  LOADING, "Loading sample"
            if re.match(r'out\d+\.urp',self.a_hardware.loaded_prog):
                return UNLOADING , "Unloading sample"
            
            # Robot Running and No sample in Gripper
            return BUSY , "Robot is in use by another module"
        
        if self.a_sample._holding_sample():
            return BUSY , "Robot is in use by another module"
        
        
        return robo_stat
    
    
    @Command()
    def stop(self,group = 'control'):
        """Stop execution of program"""
        self.a_hardware.stop()
        return    

    
    @Command(visibility = 'expert',group ='error_handling')
    def reset(self):
        """Reset storage module (removes all samples from storage)"""
        self.value = [""] * nsamples        
        
        
    
    
    
    @Command(result=None)
    def load(self):
        """load sample into storage"""
     
        
        # check if robot is ready to load sample
        if self.a_sample._holding_sample():            
            raise ImpossibleError('Gripper is already holding sample: ' + str(self.a_sample.value))
        

        slot = self.mag.get_freeSlot()

        # check for free slot
        if slot == None:
            raise ImpossibleError("No free slot available")      
                            

        
        # Run Robot script to insert actual Sample        
        prog_name = 'in'+ str(slot)+ '.urp'
        assert(re.match(r'in\d+\.urp',prog_name))
        
        self.a_hardware.run_program(prog_name)
        
        self.a_hardware.read_status()

        self.read_status()
        
        # Insert new Sample in Storage Array (it is assumed that the robot programm executed successfully)
        self.mag.insertSample("@" + str(slot))

        return
    
    

    @Command(StringType(maxchars=50),result=None)    
    def unload(self,sample_id):
        """unload sample from storage"""
        
        # check if robot is ready to load sample
        if self.a_sample._holding_sample() == True:
            raise ImpossibleError('Gripper is already holding sample' + str(self.a_sample.value)+" try unloading via 'sample' module")
            

        slot = self.mag.get_index(sample_id)

        # check if Sample is in Magazined
        if slot == None:
            raise ImpossibleError( "No sample with id "+str(sample_id)+" present Magazine " )
        
        
        

        
        # Run Robot script to unload actual Sample        
        prog_name = 'out'+ str(slot) +'.urp'
        assert(re.match(r'out\d+\.urp',prog_name))
        
        self.a_hardware.run_program(prog_name)
        
        self.a_hardware.read_status()

        self.read_status()

        try:
            self.mag.removeSample(sample_id)
        except:
            raise ImpossibleError( "No sample present: " + str(sample_id))
        
           
        return
            
    @Command(result=None)        
    def scan(self):
        """Scans every slot in storage"""
        
        
        # check if robot is ready to load sample
        if self.a_sample._holding_sample() == True:
            raise ImpossibleError('Gripper is already holding sample' + str(self.a_sample.value)+" try unloading via 'sample' module")
        

        # Run Robot script to scan Samples        
        prog_name = 'scan.urp'
        
        self.a_hardware.run_program(prog_name)
        
        #TODO start thread for communicationg with robot and updating storage array 
        
        self.a_hardware.read_status()

        self.read_status()
        

LOADING          = Storage.Status.LOADING
UNLOADING        = Storage.Status.UNLOADING
PAUSED_STORAGE   = Storage.Status.PAUSED
STOPPED_STORAGE  = Storage.Status.STOPPED
LOCAL_CONTROL    = Storage.Status.LOCAL_CONTROL 
LOCKED           = Storage.Status.LOCKED
ERROR            = Storage.Status.ERROR

PREPARING  = Storage.Status.PREPARING
DISABLED   = Storage.Status.DISABLED