import asyncio
from  frappy_HZB.samplechanger_sm import SamplechangerSM
from  frappy_HZB.storage import nsamples
from pypylon import pylon
import cv2
from qreader import QReader



class RobotServer:
    def __init__(self,samplechanger_sm:SamplechangerSM, ok_callback=None, error_callback=None):
        self.samplechanger_sm = samplechanger_sm
        self.ok_callback = ok_callback
        self.error_callback = error_callback
        #self.qcd = cv2.QRCodeDetector()
        self.qreader = QReader()
        
        try:
            tl_factory = pylon.TlFactory.GetInstance()
            camera = pylon.InstantCamera()
            camera.Attach(tl_factory.CreateFirstDevice())
            print("Camera attached")
            
            self.camera = camera
        except Exception as e:
            print(e)
            self.camera = None
            

        
          

    def set_qr_code_callback(self, qr_code_callback):
        self.qr_code_callback = qr_code_callback
        
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
        if sample_ids != ():
            print("QRCode data:")
            print(sample_ids[0])
            return sample_ids[0]
        
        #try decoding inverted image
        inv_img = cv2.bitwise_not(img)
        #cv2.imwrite(filename, inv_img)
        print("try decoding inverted image")
        sample_ids = self.qreader.detect_and_decode(image=inv_img)
        
        # if there is a QR code
        # print the data
        if sample_ids != ():
            print("QRCode data:")
            print(sample_ids[0])
            return sample_ids[0]
            
        print("Could not decode QR Code") 
        return None
    
    def grab_img(self,i=0):
        if self.camera is None:
            return None
        
        
        self.camera.Open()
        self.camera.StartGrabbing(1)
        grab = self.camera.RetrieveResult(2000, pylon.TimeoutHandling_Return)
        if grab.GrabSucceeded():
            img = grab.GetArray()
            print(f'Size of image: {img.shape}')
            

            
            
        
        self.camera.Close()
        
        return img
        

    async def handle_client(self,reader:asyncio.StreamReader, writer:asyncio.StreamWriter):
        """Handles an individual client connection."""
        addr = writer.get_extra_info('peername')
        print(f"New connection from {addr}")
        
        




        try:
            while True:
                data = await reader.readline()  # Read a line terminated by '\n'
                message = data.decode().strip()
                
                if not data:  # Connection closed
                    print(f"Connection closed by {addr}")
                    break
                
                print(f"Received line: '{message}' from {addr}")
                
                
                match message.split(":"):
                    case ['QR', slot_nr]:
                        self.samplechanger_sm.at_scan_pos()
                        print(f'Camera at QR code: {slot_nr}')
                        
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
                    case ['GET x']:
                        response = "x 1\n"
                        
                        writer.write(response.encode())  # Echo the received line
                        await writer.drain()  # Ensure data is sent

                    case ['ok']:
                        print('Received OK')
                        self.ok_callback()
                        self.samplechanger_sm.program_finished()
                        
                    case ['error', error_message]:
                        print(f'Received error: {error_message}')
                        self.error_callback(error_message)
                    case ['error']:
                        print('Received UNKNOWN error')
                        self.error_callback('')
                        
                

        except asyncio.CancelledError:
            print(f"Closing connection with {addr}")
        finally:
            writer.close()
            await writer.wait_closed()
            
    async def run_server(self,host='0.0.0.0', port=50030):
        """Creates and runs the asyncio socket server."""
        server = await asyncio.start_server(self.handle_client, host, port)
        print(f'Server running on {host}:{port}')
        async with server:
            await server.serve_forever()

    def start_server_in_thread(self):
        """Starts the asyncio server in a separate thread."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        server_coro = self.run_server()
        loop.run_until_complete(server_coro)


