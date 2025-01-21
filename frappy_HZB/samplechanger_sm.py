from statemachine import StateMachine, State



class SamplechangerSM(StateMachine):
    
    

    
    home = State('home', initial= True)
    home_next = State('home after unmounting')
    
    special_pos = State('sample_position')
    
    mounting = State('mounting Sample')
    unmounting = State('unmounting Sample')
    
    unmounting_next = State('unmounting with mounting next sample')
    
    loading = State('loading sample')
    unloading = State('unloading sample')
    

    moving_to_scan_pos = State('moving to scan position') 
    scanning_sample = State('scanning sample')
    moving_to_home_pos = State('moving to home position')
    
    running_program = State('running program')
    
    
    
    mount = (
        home.to(mounting)
        | home_next.to(mounting)
        | unmounting_next.to(mounting)
                
    )
    
    run_program = (
        home.to(running_program)
    )
    
    next = (
        home.to(mounting)
        | special_pos.to(unmounting_next)
    )
    
    
    unmount = (
        special_pos.to(unmounting)
    )
    
    unload = (
        home.to(unloading)
    )
    
    load = (
        home.to(loading)
    )
    
    program_finished = (
        mounting.to(special_pos)
        | unmounting.to(home)
        | loading.to(home)
        | unloading.to(home)
        | unmounting_next.to(home_next)
        | moving_to_home_pos.to(home)
        | running_program.to(home)
        
    )
    
    scan_samples = (
        home.to(moving_to_scan_pos)
    )
    
    at_scan_pos = (
        moving_to_scan_pos.to(scanning_sample)
    )
    
    next_slot = (
        scanning_sample.to(moving_to_scan_pos)
    )
    
    finished_scanning = (
        scanning_sample.to(moving_to_home_pos)
    )

    def set_storage(self, storage):
        self.storage_module = storage
        
    def set_special_pos(self, special_pos):
        self.special_pos_module = special_pos

    
    def on_enter_home_next(self):
        self.special_pos._mount(self.special_pos.next_sample,"mount")
        
    

