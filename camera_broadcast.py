import cv2
import socket,select
import struct
import pickle
import time
import requests
import keyboard

##Messaging service fas2sms initializations
url = "https://www.fast2sms.com/dev/bulk"
payload = "sender_id=FSTSMS&message=Intruder Alert Plz peek into your home's picam&language=english&route=p&numbers=8277075465,9110627283"
headers = {
    'authorization': "9pCyhG3MHgj4tkmN6nFWTbYJZEirLa18xoqQfR5lO0dVB2PAzD4cwOrMDPUdvoRgbKE2NiAjIHCYs97q",
    'Content-Type': "application/x-www-form-urlencoded",
    'Cache-Control': "no-cache",
    }

##Networking init
CONNECTION_LIST = []
RECV_BUFFER = 4096 # Advisable to keep it as an exponent of 2
PORT = 5000

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# this has no effect, why ?
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(("0.0.0.0", PORT))
server_socket.listen(10)
# Add server socket to the list of readable connections
CONNECTION_LIST.append(server_socket)
WRITABLE_LIST=[]
print ("server started on port " + str(PORT))

encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]


WINDOW_WIDTH = 320
WINDOW_HEIGHT = 240
LEFT_THRESH = int(WINDOW_WIDTH / 4)
RIGHT_THRESH = int(3 * WINDOW_WIDTH / 4)
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
backSub = cv2.createBackgroundSubtractorMOG2()

capture = cv2.VideoCapture(0)
firstTime=True
watching=False
while True:
    ret, frame = capture.read()


    # Resize
    frame = cv2.resize(frame, (WINDOW_WIDTH, WINDOW_HEIGHT))
    # Copy
    Display = frame.copy()
    toSend = frame.copy()
    # Draw border box on frame
    cv2.line(Display, (LEFT_THRESH, 0), (LEFT_THRESH, WINDOW_HEIGHT), (0, 255, 0))
    cv2.line(Display, (RIGHT_THRESH, 0), (RIGHT_THRESH, WINDOW_HEIGHT), (0, 255, 0))
    # Grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # Foreground mask
    if not watching:
        fgMask = backSub.apply(frame)

        ## Thresholding
        blur = cv2.GaussianBlur(fgMask,(5,5),0)
        ret1,thresh = cv2.threshold(blur,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        ## Thresholding

        ## Contours
        contours, hierarchy = cv2.findContours(thresh,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)

        for c in contours:
            moments = cv2.moments(c)
            area = cv2.contourArea(c)
            if area >= WINDOW_HEIGHT/2:
                cx = int(moments['m10'] / moments['m00'])
                cy = int(moments['m01'] / moments['m00'])
                if cx >= LEFT_THRESH and cx <= RIGHT_THRESH:
                    # cv2.drawContours(Display, [c], 0, (255,0,0), 6)

                    # NOTE: DO STUFF
                    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
                    if len(faces)>0:
                        if firstTime or time.time()-now>10:   #send a message only after 10sec dont unnecessarily irritate everytime you see a face
                            now=time.time()
                            print("Intruder check")
                            response = requests.request("POST", url, data=payload, headers=headers)
                            firstTime=False
                        
                        for (x,y,w,h) in faces:
                            cv2.rectangle(Display,(x,y),(x+w,y+h),(255,0,0),2)

                

    ## [show]
    #show the current frame and the fg masks
    # cv2.imshow("Frame Sent", frame)
    # cv2.imshow("Threshold", thresh)
    read_sockets,write_sockets,error_sockets = select.select(CONNECTION_LIST,WRITABLE_LIST,[],0)
    if len(WRITABLE_LIST)>0:
        result, toSend = cv2.imencode('.jpg', toSend, encode_param)
        for sock in write_sockets:
            #print("Insdide write"+str(len(WRITABLE_LIST)))

            
        #    data = zlib.compress(pickle.dumps(frame, 0))
            data = pickle.dumps(toSend, 0)                  #serialize the frame using picke an store the serialized object in data
            size = len(data)
            try:
                sock.sendall(struct.pack(">L", size) + data) 
            except socket.error as e:
                continue	

    for sock in read_sockets:
        #New connection
        if sock == server_socket:
            # Handle the case in which there is a new connection recieved through server_socket
            sockfd, addr = server_socket.accept()
            CONNECTION_LIST.append(sockfd)
            WRITABLE_LIST.append(sockfd)
            if len(WRITABLE_LIST)>0:
                watching=True

        
        #Some incoming message from a client
        else:
            # Data recieved from client, process it
                #In Windows, sometimes when a TCP program closes abruptly,
                # a "Connection reset by peer" exception will be thrown
            data = sock.recv(RECV_BUFFER)
            if data.decode()=='q':
                CONNECTION_LIST.remove(sock)
                WRITABLE_LIST.remove(sock)
                if len(WRITABLE_LIST)==0:
                    watching=False
    cv2.imshow("Display",Display)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break     
capture.release()
print("Out of here")
server_socket.close()
cv2.destroyAllWindows()
