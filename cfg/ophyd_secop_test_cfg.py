#####################################################################
# Python version of frappy config
#####################################################################

Node('ophyd_secop.frappy.demo',
    'short description\n\n'
    'This is a very long description providing all the gory details '
    'about the stuff we are describing.',
    'tcp://10771',
    more="blub",
)

Mod('str_test',
    'frappy_HZB.ophyd_secop_test_modules.Test_Mod_str',
    'test module for reading String signals in Bluesky RE',
    group='test',
    value = 'blah'
    
)


Mod('struct_of_arrays',
    'frappy_HZB.ophyd_secop_test_modules.Test_Struct_of_arrays',
    'module for testing struct of arrays',
    value = {
        'ints':[1,2,3,4,5],
        'strings':['aaaa','aaaaa','aaaa','aaa','aa'],
        'floats':[1.1,2.2,4.3,6.4,7.5]},
    

    writable_strct_of_arr = {
        'ints':[1,2,3,4,5],
        'strings':['aaaa','aaaaa','aaaa','aaa','aa'],
        'floats':[1.1,2.2,4.3,6.4,7.5]}
    
)




Mod('nd_arr',
    'frappy_HZB.ophyd_secop_test_modules.Test_ND_arrays',
    'module for testing multidimensional arrays',
    value = [[1,1,1,1,1],
             [1,1,1,1,1],
             [1,1,1,1,1],
             [1,1,1,1,1],
             [1,1,1,1,1]
             ],
    arr3d = [[[0]]]

)





    
Mod('ophy_struct',
    'frappy_HZB.ophyd_secop_test_modules.OPYD_test_struct',
    'simulated hardware for testing ophyd struct behavior'
    'also tuples',
    group='very important/stuff',
    #jitter=0.1,
    p_start=5,
    looptime=1,
    value= {'x':10,'y':10,'z':10,'color':'blue'},
    target= {'x':10,'y':10,'z':10,'color':'blue'},

    nested_struct = {
        'number':5,
        'string':'blablalbla',
        'tupl':[1,1,1],
        'pos_struct':{
            'x':5,
            'y':10,
            'z':15,
            'col':'green',
            'enum':1

        }
    
    },
    tuple_param = (5,5,5,'green')
    #ramp=6,
    #maxpower=20.0,
    #heater=4.1,
    #mode='pid',
    #tolerance=0.1,
    #window=30,
    #timeout=900,
    #p = Param(40, unit='%/K'),  # in case 'default' is the first arg, we can omit 'default='
    #i = 10,
    #d = 2,
    #pid = Group('p', 'i', 'd'),
    #pollinterval = Param(export=False),
    #value = Param(unit = 'K', test = 'customized value'),
)