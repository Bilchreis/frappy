
import re
import uuid

from frappy.core import BUSY, IDLE, Command, Drivable, HasIO, IntRange, \
    Parameter, Readable, StructOf
from frappy.datatypes import ArrayOf, EnumType, FloatRange, StatusType, \
    StringType
from frappy.errors import ImpossibleError, IsBusyError
from frappy.lib.enum import Enum
from frappy.modules import Attached

from frappy_HZB.samplechanger_sm import SamplechangerSM

nsamples = 6

EMPTY_SLOT = ""


class Magazin:

    
    def __init__(self,nSamples):
        self.samples = [""] * nSamples
        self._next_sample_gen = self.next_sample_generator()
          
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
        
        self.samples[slot] = sample_id
            
    
            
    def next_sample_generator(self):
        """
        Generator method to yield the next non-empty sample, looping continuously.
        If all slots are empty, it yields None once and stops.
        """
        n_samples = len(self.samples)
        if all(sample == EMPTY_SLOT for sample in self.samples):
            yield None
            

        index = 0
        while True:
            if self.samples[index] != EMPTY_SLOT:
                yield self.samples[index]
            index = (index + 1) % n_samples

    def get_next_sample(self):
        """
        Method to return the next non-empty sample using the generator.
        """
        return next(self._next_sample_gen)

            


            



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
                    readonly = True,
                    default = [""] * nsamples)
    
    
    
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.mag = Magazin(nsamples)
        self.a_hardware.sm.set_storage(self)
        self.a_hardware.robo_server.set_qr_code_callback(self.set_new_sampleID)
        
        self.inserted_sample = None
        self.unloaded_sample = None

        self.callbacks = [
            ('ok','load',self.load_ok_callback),
            ('error','load',self.load_error_callback),
            ('ok','unload',self.unload_ok_callback),
            ('error','unload',self.unload_error_callback),
            ('ok','scan_samples',self.scan_ok_callback),
            ('error','scan_samples',self.scan_error_callback),
        ]
        
        self.a_hardware.robo_server.add_callbacks(self.callbacks)
        
    def read_value(self):
        return self.mag.samples    
        
    def read_status(self):
        robo_state = self.a_hardware.sm.current_state
        
        if robo_state in  [SamplechangerSM.home,SamplechangerSM.home_mounted]:
            return IDLE, "ready for commamnds"
        
        
        if robo_state in [SamplechangerSM.loading,SamplechangerSM.loading_mounted]:
            return LOADING, "loading sample"
        
        if robo_state in  [SamplechangerSM.unloading,SamplechangerSM.unloading_mounted]:
            return UNLOADING, "unloading sample"

        return BUSY, "robot is busy: " + robo_state.id
        
    def set_new_sampleID(self,slot,sample_id):
        self.mag.updateSample(slot,sample_id)
    
    
    @Command()
    def stop(self,group = 'control'):
        """Stop execution of program"""
        self.a_hardware.stop()
        return    

    
    @Command(visibility = 'expert',group ='error_handling')
    def reset(self):
        """Reset storage module (removes all samples from storage)"""
        self.value = [""] * nsamples        
        
        
    def load_ok_callback(self):
        
        self.mag.insertSample("@" + str(self.inserted_sample))
        return
    
    def load_error_callback(self,error_message= None):
        self.a_hardware.error_occured(error_message)
        self.read_status()
    
    @Command(result=None)
    def load(self):
        """load sample into storage"""

        if self.a_hardware.sm.current_state not in  [SamplechangerSM.home,SamplechangerSM.home_mounted]:
            raise ImpossibleError('Robot is currently not in home position, cannot load sample')
        
        


        slot = self.mag.get_freeSlot()

        # check for free slot
        if slot == None:
            raise ImpossibleError("No free slot available")      
                            

        
        # Run Robot script to insert actual Sample        
        prog_name = 'in'+ str(slot)+ '.urp'
        assert(re.match(r'in\d+\.urp',prog_name))
        
        self.inserted_sample = f'@{str(slot)}'
        self.a_hardware.run_program(prog_name,"load")
        
        self.a_hardware.read_status()

        self.read_status()
        
        # Insert new Sample in Storage Array (it is assumed that the robot programm executed successfully)
        

        return
    
    
    def unload_ok_callback(self):
        try:
            self.mag.removeSample(self.unloaded_sample)
        except:
            raise ImpossibleError( "No sample present: " + str(self.unloaded_sample))        
           
        return
    
    def unload_error_callback(self,error_message= None):
        self.a_hardware.error_occured(error_message)
        self.read_status()
        
        
    @Command(StringType(maxchars=50),result=None)    
    def unload(self,sample_id):
        """unload sample from storage"""

        

        if self.a_hardware.sm.current_state not in  [SamplechangerSM.home,SamplechangerSM.home_mounted]:
            raise ImpossibleError('Robot is currently not in home position, cannot unload sample')
        

        slot = self.mag.get_index(sample_id)

        # check if Sample is in Magazine
        if slot == None:
            raise ImpossibleError( "No sample with id "+str(sample_id)+" present Magazine " )
        
        
        

        
        # Run Robot script to unload actual Sample        
        prog_name = 'out'+ str(slot) +'.urp'
        assert(re.match(r'out\d+\.urp',prog_name))
        
        self.unloaded_sample = sample_id
        
        self.a_hardware.run_program(prog_name,"unload")
        
        self.a_hardware.read_status()

        self.read_status()

        return
    
    
    def scan_ok_callback(self):
        return
    
    def scan_error_callback(self,error_message= None):
        self.a_hardware.error_occured(error_message)
        self.read_status()
            
    @Command(result=None)        
    def scan(self):
        """Scans every slot in storage"""
        

        if self.a_hardware.sm.current_state not in  [SamplechangerSM.home,SamplechangerSM.home_mounted]:
            raise ImpossibleError('Robot is currently not in home position, cannot scan samples')

        # Run Robot script to scan Samples        
        prog_name = 'Scan_mag.urp'
        
        self.a_hardware.run_program(prog_name,"scan_samples")
        
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