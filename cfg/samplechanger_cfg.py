nsamples = 12

Node('sample_changer.HZB',  # a globally unique identification
     'Sample Changer\n\nThis is an demo for a  SECoP (Sample Environment Communication Protocol) sample changer SEC-Node.',  # describes the node
      'tcp://10803',
      implementor = 'Peter Wegmann')  # you might choose any port number > 1024

Mod('robot_io',  # the name of the module
    'frappy_HZB.hardware.RobotIO',  # the class used for communication
    'TCP communication to robot Dashboard Server Interface',  # a description
    uri='tcp://192.168.3.5:29999',  # the serial connection
)    
    
Mod('hardware',
    'frappy_HZB.hardware.hardware',
    'The hardware component responsible for physically moving the samples',
    io='robot_io',

    
    model = "none",
    serial = "none",
    ur_version = "none",
    
   
    pollinterval = 0.1,

)


Mod('storage',
    'frappy_HZB.storage.Storage',
    'Hardware component that holds a number of samples in sample slots',
    io ='robot_io',
    a_sample = 'sample_at_measurement_position',
    a_hardware = 'hardware',
    pollinterval = 1
  
)


Mod('sample_at_measurement_position',
    'frappy_HZB.special_position.Special_Position',
    'Sample currently present at the measuerement position',
    io ='robot_io',
    a_hardware = 'hardware',
    a_storage = 'storage',
    pollinterval = 1,

    )
