import re

from frappy.core import BUSY, ERROR, IDLE, Command, HasIO, Parameter, \
    Readable, StatusType, StringIO, StructOf
from frappy.datatypes import ArrayOf, BoolType, EnumType, FloatRange, \
    StringType
from frappy.errors import ImpossibleError, InternalError, IsBusyError, \
    IsErrorError, ReadFailedError
from frappy.lib.enum import Enum
from frappy.modules import Attached

from frappy_HZB.samplechanger_sm import SamplechangerSM
from frappy_HZB.robot_server import RobotServer
from frappy.lib import clamp, mkthread


import time

ROBOT_MODE_ENUM = {
    'NO_CONTROLLER'  :0,
    'DISCONNECTED'   :1,
    'CONFIRM_SAFETY' :2,
    'BOOTING'        :3,
    'POWER_OFF'      :4,
    'POWER_ON'       :5,
    'IDLE'           :6,
    'BACKDRIVE'      :7,
    'RUNNING'        :8          
}

SAFETYSTATUS = {
    'NORMAL' :0,
    'REDUCED' :1,
    'PROTECTIVE_STOP' :2,
    'RECOVERY' :3,
    'SAFEGUARD_STOP' :4,
    'SYSTEM_EMERGENCY_STOP' :5,
    'ROBOT_EMERGENCY_STOP' :6,
    'VIOLATION' :7,
    'FAULT' :8,
    'AUTOMATIC_MODE_SAFEGUARD_STOP' :9,
    'SYSTEM_THREE_POSITION_ENABLING_STOP' :10,
    'UNKNOWN':11

} 



class hardware(HasIO,Readable):    
    
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.sm = SamplechangerSM()
        self.callbacks = [
            ('ok','run_program',self.run_program_ok_callback),
            ('error', 'run_program',self.run_program_error_callback)
        ]
        self.robo_server = RobotServer(self.sm,self.callbacks,logger=self.log)
        self.sm.set_wait_idle_callback(self.wait_idle_cb)  


    

    Status = Enum( 
        Readable.Status,
        DISABLED = StatusType.DISABLED,
        STANDBY = StatusType.STANDBY,
        BUSY     = StatusType.BUSY,
        PAUSED = 305,
        PREPARING = StatusType.PREPARING,
        STOPPED = 402,
        LOCAL_CONTROL = 403,
        LOCKED = 404,        
        UNKNOWN = StatusType.UNKNOWN                
        )  #: status codes
    
    def initModule(self):
        super().initModule()
        self._thread = mkthread(self.robo_server.start_server_in_thread)

    status = Parameter(datatype=StatusType(Status))  # override Readable.status

    
    
    value = Parameter("Currently loaded program",
                       datatype=StringType(),
                       default = '<unknown>.urp',
                       readonly = True)
    
    loaded_prog = Parameter("Program that is currently loaded",
                            datatype= StringType(),
                            default = "<unknown>.urp",
                            readonly = True,
                            visibility = 'expert')
    
    model = Parameter("Model name of the robot",
                      datatype=StringType(),
                      default = "none",                
                      readonly = True,
                      group = "Robot Info")
    
    serial = Parameter("Serial number of connected robot",
                       datatype=StringType(),
                       default = "none",
                       readonly = True,
                       group = "Robot Info")
    
    ur_version = Parameter("Version number of the UR software installed on the robot",
                           datatype=StringType(),
                           default = "none",
                           readonly = True,
                           group = "Robot Info",
                           visibility = 'expert')
    
    robotmode = Parameter("Current mode of robot",
                          datatype=EnumType("Robot Mode",ROBOT_MODE_ENUM),
                          default = "DISCONNECTED",
                          readonly = True,
                          group = "Status Info")
    
    powerstate = Parameter("Powerstate of robot",
                           datatype=EnumType("Pstate",POWER_OFF= None,POWER_ON = None ),
                           default = "POWER_OFF" ,
                           readonly = False,
                           group = "Status Info")
    
    safetystatus = Parameter("Safetystatus: Specifying if a given Safeguard Stop was caused by the permanent safeguard I/O stop,a configurable I/O automatic mode safeguard stop or a configurable I/O three position enabling device stop.",
                             datatype=EnumType(SAFETYSTATUS),
                             default = "NORMAL",
                             readonly = True,
                             group = 'Status Info')

    
    program_running = Parameter("Program running status",
                                datatype=BoolType,
                                default = False,
                                readonly = True,
                                group = 'Status Info')
    
    was_running = Parameter("Last Program running status",
                                datatype=BoolType,
                                default = False,
                                readonly = True,
                                export = False
                                )

    

    
    is_in_remote_control = Parameter("Control status of robot arm",
                                     datatype=BoolType,
                                     readonly = True,
                                     default = False,
                                     group = 'Status Info')
       
    def wait_idle_cb(self):

        timeout = time.time() + 5   # 5 Second Timeout
        while self._program_running():
            if time.time() > timeout:
                raise Exception("timeout")
            time.sleep(0.2)
            
                    
        self.read_status()
            
        

       
    
    def doPoll(self):
        self.read_value()
        self.read_status()



  



    def read_safetystatus(self):
        return 'NORMAL'

   
    

    def read_loaded_prog(self):
        return self.loaded_prog

        
    
    def read_value(self):
        return self.read_loaded_prog()



    def read_model(self):
        return "UR5"

    def read_serial(self):
        return "I_AM_A_SERIAL_NUMBER"
    

    def read_ur_version(self):
        return "V212323243"
    
    def read_robotmode(self):
        "IDLE"
    
    def read_powerstate(self):
        return 'POWER_ON' 

    
    
    def write_powerstate(self,powerstate):
        p_str = powerstate.name
        
        self.communicate(POWER_STATE.get(p_str,None))
        
        if powerstate == 'POWER_ON':
            self.communicate('brake release')
        
        
        self.powerstate = self.read_powerstate()
        
        return powerstate.name

    
    def read_status(self):               
       
        if self.status[0] == STOPPED:
            return self.status
                
        if self.status[0] == ERROR:
            return self.status

        if self.sm.current_state == SamplechangerSM.home or self.sm.current_state == SamplechangerSM.home_mounted:
            return IDLE, 'Robot is at home position'
        else:
            return BUSY, f'Robot is running program. Robot State: {self.sm.current_state.name}'

        
        



    def read_program_running(self):
        running = True
        
        if self.sm.current_state == SamplechangerSM.home or self.sm.current_state == SamplechangerSM.home_mounted:
            running = False

        
        self.was_running = running
        
        
        return running 

  


    @Command(group ='control')
    def stop(self):
        """Stop execution of program"""
        
        # already stopped
        if self.status[0] == STOPPED:
            raise ImpossibleError('module is already stopped')

        if self._program_running():  
            self.status = STOPPED, "Stopped execution"
                

    def run_program(self,program_name,sm_event):

        if self.status[0] == BUSY or self.status[0] == PREPARING:
            if not self._program_running() and self.sm.current_state == SamplechangerSM.home_switch:
                pass
            else:
                raise IsBusyError('Robot is already executing another program')
        
        if self.status[0] >= 400 and self.status[0] != STOPPED:
            raise IsErrorError("Robot is in an error state. program '"+program_name+ "' cannot be exectuted")
        
        
        self.loaded_prog = program_name
        
        self.status = BUSY, "Starting program"      

        self.sm.send(sm_event)
    

    def error_occurred(self,error_message):
        if error_message:
            self.status = ERROR, f'Reason:{error_message}'
        else:
            self.status = ERROR, 'An unknown error occurred' 
        
        self.read_status()
   
    def run_program_ok_callback(self):
        # Robot successfully unmounted the sample
        pass
    
    def run_program_error_callback(self,message):
        # Error while running program
        self.status = ERROR, message
        self.read_status()
   
   
    @Command(StringType(maxchars=40),group = 'control')
    def run_program_by_path(self,program_name):
        """Runs the requested program on the robot"""
        self.run_program(program_name,'run_program')

        
    
  


            
            
    
  
PAUSED           = hardware.Status.PAUSED
STOPPED          = hardware.Status.STOPPED
UNKNOWN          = hardware.Status.UNKNOWN
PREPARING        = hardware.Status.PREPARING
DISABLED         = hardware.Status.DISABLED
STANDBY          = hardware.Status.STANDBY 
LOCAL_CONTROL    = hardware.Status.LOCAL_CONTROL 
LOCKED           = hardware.Status.LOCKED
ERROR            = hardware.Status.ERROR

ROBOT_MODE_STATUS = {
    'NO_CONTROLLER' :(ERROR,'NO_CONTROLLER'),
    'DISCONNECTED' :(DISABLED,'DISCONNECTED'),
    'CONFIRM_SAFETY' :(DISABLED,'CONFIRM_SAFETY'),
    'BOOTING' :(PREPARING,'BOOTING'),
    'POWER_OFF' :(DISABLED,'POWER_OFF'),
    'POWER_ON' :(STANDBY,'POWER_ON'),
    'IDLE' :(IDLE,'IDLE'),
    'BACKDRIVE' :(PREPARING,'BACKDRIVE'),
    'RUNNING' :(IDLE,'IDLE'),
}



POWER_STATE = {
    'POWER_ON'  : 'power on',
    'POWER_OFF' : 'power off'
}


