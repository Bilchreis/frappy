import asyncio
from  frappy_HZB.samplechanger_sm import SamplechangerSM
from  frappy_HZB.storage import nsamples
from pypylon import pylon
import cv2
from qreader import QReader



class RobotServer:
    def __init__(self,samplechanger_sm:SamplechangerSM, callbacks = [],logger=None):
        self.samplechanger_sm = samplechanger_sm
        self.callbacks = callbacks
        #self.qcd = cv2.QRCodeDetector()
        self.qreader = QReader()
        self.log = logger
        
        try:
            tl_factory = pylon.TlFactory.GetInstance()
            camera = pylon.InstantCamera()
            camera.Attach(tl_factory.CreateFirstDevice())

            self.log.info("Camera attached")
            
            self.camera = camera
        except Exception as e:
            self.log.error(e)
            self.camera = None
            

    def run_OK_callbacks(self,cb_arg = None): 
        self.log.info(f"Running OK callbacks, current State: {self.samplechanger_sm.current_state.id}")       
        for callback_tuple in self.callbacks:
            match callback_tuple:
                case ('ok',self.samplechanger_sm.current_state.value, callback):
                    if cb_arg is not None:
                        callback(cb_arg)
                    else:
                        callback()
                        

    def run_error_callbacks(self,cb_arg = None):        
        for callback_tuple in self.callbacks:
            match callback_tuple:
                case ('error',self.samplechanger_sm.current_state.value, callback):
                    if cb_arg is not None:
                        callback(cb_arg)
                    else:
                        callback()

    def add_callbacks(self,callbacks):
        self.callbacks.extend(callbacks)
          

    def set_qr_code_callback(self, qr_code_callback):
        self.qr_code_callback = qr_code_callback
        
        
    def set_presence_detection_callback(self, presence_detection_callback):
        self.presence_detection_callback = presence_detection_callback
        
    def decode_img(self,img,i= 0):         

        # initialize the cv2 QRCode detector
        #crop_img = img#[500:2200,img = cv2.bitwise_not(thresh, thresh) 500:2200]
        #filename = "saved_qr_img_%d.png" % i
        #cv2.imwrite(filename, img)
        
        # detect and decode
        sample_ids = self.qreader.detect_and_decode(image=img)
        #retval, decoded_info, points, straight_qrcode = self.qcd.detectAndDecodeMulti(img)
        # if there is a QR code
        # print the data
        
                
        if sample_ids != () and sample_ids != (None,):
            self.log.info(f"QRCode data: {sample_ids[0]}")
            return sample_ids[0]
        
        #try decoding inverted image
        inv_img = cv2.bitwise_not(img)
        #cv2.imwrite(filename, inv_img)
        self.log.info("try decoding inverted image")
        sample_ids = self.qreader.detect_and_decode(image=inv_img)
        
        # if there is a QR code
        # print the data
        if sample_ids != ():
            self.log.info(f"QRCode data: {sample_ids[0]}")
            return sample_ids[0]
            
        self.log.error("No QR code found") 
        return None
    
    def grab_img(self,i=0):
        if self.camera is None:
            return None
        
        
        self.camera.Open()
        self.camera.StartGrabbing(1)
        grab = self.camera.RetrieveResult(2000, pylon.TimeoutHandling_Return)
        if grab.GrabSucceeded():
            img = grab.GetArray()           
            
        
        self.camera.Close()
        
        return img
        

    async def handle_client(self,reader:asyncio.StreamReader, writer:asyncio.StreamWriter):
        """Handles an individual client connection."""
        addr = writer.get_extra_info('peername')
        self.log.info(f"New connection from Robot: {addr}")
        
        
        




        try:
            while True:
                data = await reader.readline()  # Read a line terminated by '\n'
                message = data.decode().strip()
                
                if not data:  # Connection closed
                    self.log.info(f"Connection closed by {addr}")
                    break
                
                self.log.info(f"Received line: '{message}' from {addr}")
                
                
                match message.split(":"):
                    case ['Slot', slot_nr,detected]:
                        
                        self.presence_detection_callback(int(slot_nr) -1,int(detected))
                             
                    
                        if int(slot_nr) == nsamples:
                            self.samplechanger_sm.finished_presence_detection()
                        else:
                            self.samplechanger_sm.next_slot()
                    case ['QR', slot_nr]:
                        if self.samplechanger_sm.current_state == SamplechangerSM.moving_to_scan_pos:
                            self.samplechanger_sm.at_scan_pos()
                            self.log.info(f'Camera at QR code: {slot_nr}')
                            
                            #await asyncio.sleep(0.5)
                            
                            if self.camera != None:
                                img = self.grab_img(int(slot_nr))
                                qr_data = self.decode_img(img,int(slot_nr))
                                
                                if qr_data is not None:
                                    self.qr_code_callback(int(slot_nr) -1 ,qr_data)                        
                                
                
                            if int(slot_nr) == nsamples:
                                self.samplechanger_sm.finished_scanning()
                            else:
                                self.samplechanger_sm.next_slot()
                                
                        if self.samplechanger_sm.current_state == SamplechangerSM.mounting:
                            self.log.info(f'Camera at QR code: {slot_nr}')
                            
                            #await asyncio.sleep(0.5)
                            
                            if self.camera != None:
                                img = self.grab_img(int(slot_nr))
                                qr_data = self.decode_img(img,int(slot_nr))
                                
                                
                                #TODO check if QR code is different to the one in storage!!!
                                self.log.info(f'QR code: {qr_data} at slot {slot_nr}')                  

                

                            
                    case ['GET x']:
                        response = "x 1\n"
                        
                        writer.write(response.encode())  # Echo the received line
                        await writer.drain()  # Ensure data is sent

                    case ['ok']:
                        self.log.info('Received OK')
                        self.run_OK_callbacks()
                        self.samplechanger_sm.program_finished()
                        
                    case ['error', error_message]:
                        self.log.error(f'Received error: {error_message}')
                        self.run_error_callbacks(error_message)
                    case ['error']:
                        self.log.error('Received UNKNOWN error')
                        self.run_error_callbacks()
                        
                

        except asyncio.CancelledError:
            self.log.error(f"Closing connection with {addr}")
        finally:
            writer.close()
            await writer.wait_closed()
            
    async def run_server(self,host='0.0.0.0', port=50030):
        """Creates and runs the asyncio socket server."""
        server = await asyncio.start_server(self.handle_client, host, port)
        self.log.info(f'Server running on {host}:{port}')
        async with server:
            await server.serve_forever()

    def start_server_in_thread(self):
        """Starts the asyncio server in a separate thread."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        server_coro = self.run_server()
        loop.run_until_complete(server_coro)


