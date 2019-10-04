import socket,sys
import sys
import cv2
import pickle
import numpy as np
import struct ## new
import zlib


#main function
if __name__ == "__main__":
	
	
	host = "127.0.0.1"
	port = 5000
	
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.settimeout(100)
	# connect to remote host
	try :
		s.connect((host, port))
	except :
		print ('Unable to connect')
		sys.exit()
	
	print ('Connected to remote host. Start sending messages')
	data = b""
	payload_size = struct.calcsize(">L")
	while 1:
		#incoming message from remote server
		while len(data) < payload_size:
				data += s.recv(4096)

		packed_msg_size = data[:payload_size]
		data = data[payload_size:]
		msg_size = struct.unpack(">L", packed_msg_size)[0]
		while len(data) < msg_size:
			data += s.recv(4096)
		frame_data = data[:msg_size]
		data = data[msg_size:]

		frame=pickle.loads(frame_data)
		frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
		cv2.imshow('ImageWindow',frame)
		if cv2.waitKey(1) & 0xFF == ord('q'):
			s.send(b'q')
			break
	s.close()
	cv2.destroyAllWindows()
