
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


      



class Special_Position(HasIO,Drivable):
    
    Status = Enum(Drivable.Status,
                  DISABLED = StatusType.DISABLED,
                  PREPARING = StatusType.PREPARING,
                  HOLDING_SAMPLE = 101, 
                  MOUNTING=301,
                  UNMOUNTING = 302,
                  UNLOADING = 304,
                  MEASURING = 303,
                  PAUSED = 305,
                  UNKNOWN = 401,
                  STOPPED = 402,
                  LOCAL_CONTROL = 403,
                  LOCKED = 404 
                  )  #: status codes

    status = Parameter(datatype=StatusType(Status))  
    
    
    a_hardware = Attached(mandatory = True)
    a_storage   = Attached(mandatory = True)
    
    value = Parameter("ID of the sample currently present at " +
                      "the position ('' means that the Position is empty)",
                    datatype=StringType(maxchars=50),
                    readonly = True)
    
    target = Parameter("ID of the sample that should be moved to the position ",
                       datatype=StringType(50)) 
    
    
    def write_target(self,target):               
        
        if target == "":            
            ### Unmount:
            return self._unmount(target)
        else:                   
           ### Mount:
           return self._mount(target)
       
       
    def _mount(self,target):
        """Mount Sample to Robot arm"""
        assert(target != "")
        
        # check if robot is currently holding a Sample from Storage
        if self._holding_sample():
            raise ImpossibleError('Gripper is already holding sample' + str(self.value))   
        
        # check if sample is present in Storage
        if self.a_storage.mag.get_index(target) == None:
            raise ImpossibleError('no sample with ID: ' +str(target)+' in storage! please, check sample objects stored in storage')
              
    
     
        # Run Robot script to mount actual Sample        
        prog_name = 'messpos'+ str(target) + '.urp'
        
        assert(re.match(r'messpos\d+\.urp',prog_name) )
        
        self.a_hardware.run_program(prog_name)
 
        self.status = MOUNTING , "Mounting Sample: " + str(target)
        
        self.target = target
        
        # Robot successfully mounting the sample
        self.value = self.target
        
        self.read_status()
        
        return target
     

    def _unmount(self,target):
        """Unmount Sample to Robot arm"""
        
        assert(target == "")
        
        
        # check if robot is ready to mount sample
        if not self._holding_sample():
            raise ImpossibleError('Gripper is currently not holding a sample, cannot unmount')  
        
        if self.a_storage.mag.get_index(target) == None:
            raise ImpossibleError('no sample with ID: ' +str(target)+' in storage! please, check sample objects stored in storage')
                    
        
        # Run Robot script to unmount Sample        
        prog_name = 'messposin'+ str(self.value) + '.urp'
        
        assert(re.match(r'messposin\d+\.urp',prog_name) )
        
        self.a_hardware.run_program(prog_name)

        self.status = UNMOUNTING , "Unmounting Sample: " + str(self.value)
        
        self.target = target
        # Robot successfully unmounted the sample
        self.value = 0
        
        self.read_status()
        
        return target

                  
       


    def _holding_sample(self):
        return True if self.value == ""  else False


        
    def read_status(self):
            robo_stat = self.a_hardware.status
            
            
            # Robot Idle and sample in Gripper
            if robo_stat[0] == IDLE and self._holding_sample():
                
                return HOLDING_SAMPLE , "IDLE with Sample in Gripper"
            
            # Robot Arm is Busy        
            if robo_stat[0] == BUSY:
                if re.match(r'messpos\d+\.urp',self.attached_robot.value):
                    return  MOUNTING, "Mounting Sample"
                if re.match(r'messposin\d+\.urp',self.attached_robot.value):
                    return UNMOUNTING , "Unmounting Sample"
                if re.match(r'messen+\.urp',self.attached_robot.value):
                    return MEASURING , "Measuring Sample"
                
                # Robot Running and No sample in Gripper
                return BUSY , "Robot is in use by other module"
            
            return robo_stat
        
    @Command()
    def next(self):
        """  (removes (if necessary) old sample and mounts next sample, same as setting 
        the target first to '' and then to 'sampleID')"""
        pass   
        
    @Command()
    def stop(self,group = 'control'):
        """Stop execution of program"""
        self.a_hardware.stop()
        return    

    
    
MOUNTING         = Special_Position.Status.MOUNTING
UNMOUNTING       = Special_Position.Status.UNMOUNTING
MEASURING        = Special_Position.Status.MEASURING
HOLDING_SAMPLE   = Special_Position.Status.HOLDING_SAMPLE
PAUSED_SAMPLE    = Special_Position.Status.PAUSED
STOPPED_SAMPLE   = Special_Position.Status.STOPPED