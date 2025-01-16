nsamples = 12

Node('sample_changer.HZB',  # a globally unique identification
     'Sample Changer\n\nThis is an demo for a  SECoP (Sample Environment Communication Protocol) sample changer SEC-Node.',  # describes the node
      'tcp://10803',
      implementor = 'Peter Wegmann')  # you might choose any port number > 1024

Mod('robot_io',  # the name of the module
    'frappy_HZB.hardware.RobotIO',  # the class used for communication
    'TCP communication to robot Dashboard Server Interface',  # a description
    uri='tcp://localhost:29999',  # the serial connection
)    
    
Mod('hardware',
    'frappy_HZB.hardware.hardware',
    'The hardware component responsible for physically moving the samples',
    io='robot_io',

    
    model = "none",
    serial = "none",
    ur_version = "none",
    
   
    pollinterval = 0.1,
    stop_State = {'stopped' : False,'interrupted_prog' : 'none'},
    pause_State = {'paused' : False,'interrupted_prog' : 'none'}

)



