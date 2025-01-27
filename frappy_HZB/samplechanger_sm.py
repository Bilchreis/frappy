from statemachine import StateMachine, State, Event



class SamplechangerSM(StateMachine):
    
    

    
    home = State('home', initial= True)    
    home_mounted = State('home:[mounted]')
    
    mounting = State('mounting Sample')
    
    unmounting = State('unmounting Sample',)
    unmounting_switch = State('unmounting Sample:[switch]')
    

    
    loading = State('loading sample')
    loading_mounted = State('loading:[mounted]')
    
    unloading = State('unloading sample','unload')
    unloading_mounted = State('unloading:[mounted]')
    

    moving_to_scan_pos = State('moving to scan position') 
    moving_to_scan_pos_mounted = State('moving to scan position:[mounted]')
    
    scanning_sample = State('scanning sample')
    scanning_sample_mounted = State('scanning sample:[mounted]')
    
    moving_to_home_pos = State('moving to home position')
    moving_to_home_mounted_pos = State('moving to home position:[mounted]')
    
    presence_detection = State('presence detection')
    presence_detection_mounted = State('presence detection:[mounted]')
    
    

    
    
    
    running_program = State('running program','run_program')

    
    home_switch = State('home:[switch]')
    
    
    
    mount = (
        home.to(mounting)
        | home_mounted.to(unmounting_switch)
        | home_switch.to(mounting)
        

                
    )

    

    
    run_program = (
        home.to(running_program)

    )
    
    
    
    unmount = (
        home_mounted.to(unmounting)
    )
    
    
    
    unload = (
        home.to(unloading)
        | home_mounted.to(unloading_mounted)
    )
    
    load = (
        home.to(loading)
        | home_mounted.to(loading_mounted)
    )
    
    program_finished = (
        unmounting.to(home)
        | mounting.to(home_mounted)
        | loading.to(home)
        | loading_mounted.to(home_mounted)
        | unloading.to(home)
        | unloading_mounted.to(home_mounted)
        | moving_to_home_pos.to(home)
        | moving_to_home_mounted_pos.to(home_mounted)
        | running_program.to(home)
        | unmounting_switch.to(home_switch)
        
    )
    
    scan_samples = (
        home.to(moving_to_scan_pos)
        | home_mounted.to(moving_to_scan_pos_mounted)
    )
    
    at_scan_pos = (
        moving_to_scan_pos.to(scanning_sample)
        | moving_to_scan_pos_mounted.to(scanning_sample_mounted)
    )
    
    next_slot = (
        scanning_sample.to(moving_to_scan_pos)
        | scanning_sample_mounted.to(moving_to_scan_pos_mounted)
        | presence_detection.to.itself()
        | presence_detection_mounted.to.itself()
    )
    
    finished_scanning = (
        scanning_sample.to(presence_detection)
        | scanning_sample_mounted.to(presence_detection_mounted)
    )
    

    
    finished_presence_detection = (
        presence_detection.to(moving_to_home_pos)
        | presence_detection_mounted.to(moving_to_home_mounted_pos)
    )

    def set_storage(self, storage):
        self.storage_module = storage
        
    def set_special_pos(self, special_pos):
        self.special_pos_module = special_pos

    
    def on_enter_home_switch(self):
        self.special_pos_module._mount("mount",self.special_pos_module.next_sample)
        
    def on_transition(self, event_data, event: Event):
        # The `event` parameter can be declared as `str` or `Event`, since `Event` is a subclass of `str`
        # Note also that in this example, we're using `on_transition` instead of `on_cycle`, as this
        # binds the action to run for every transition instead of a specific event ID.
        print(f'State: {self.current_state.id} incoming Event: {event.id}' )
        
    

#sm = SamplechangerSM()

#sm._graph().write_png('samplechanger.png')