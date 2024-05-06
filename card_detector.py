
from picamera2 import Picamera2, Preview
from inference_sdk import InferenceHTTPClient
import time
import math

#server imports
from socket import *
from time import ctime
import jpysocket


#server setup
HOST = ''
PORT = 21567
BUFSIZE = 1024
ADDR = (HOST,PORT)


im_height = 2464
im_width = 3280
filepath = "input.jpg"

# optimal move table for edge cases -  0 - hit 1 - double 2 - stay 
next_move=[[0,1,1,1,1,0,0,0,0,0],
        [1,1,1,1,1,1,1,1,0,0],
        [1,1,1,1,1,1,1,1,1,1],
        [0,0,2,2,2,0,0,0,0,0],
        [2,2,2,2,2,0,0,0,0,0],
        [2,2,2,2,2,0,0,0,0,0],
        [2,2,2,2,2,0,0,0,0,0],
        [2,2,2,2,2,0,0,0,0,0]]

#translation dictionary 
cardVals = {'2':2, '3':3, '4':4, '5':5, '6':6, '7':7, '8':8, '9':9, '10':10, 'J':10, 'Q':10, 'K':10, 'A':11}

# server socket setup
tcpSerSock = socket(AF_INET, SOCK_STREAM)
tcpSerSock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
tcpSerSock.bind(ADDR)
tcpSerSock.listen(5)

# picam setup
picam2 = Picamera2()
camera_config = picam2.create_still_configuration(main={"size": (im_width, im_height)})
picam2.configure(camera_config)
picam2.start_preview(Preview.DRM)
picam2.start()
time.sleep(2)


def get_next_move():
    # capture what the camera sees
    picam2.capture_file(filepath)

    CLIENT = InferenceHTTPClient(
        api_url="https://detect.roboflow.com",
        api_key="ROZzwN49JaviKrzpqJcG"
    )

    # send picture to the roboflow API
    result = CLIENT.infer(filepath, model_id="playing-cards-ow27d/4")

    print(result)
    for i in result['predictions']:
        print(i['class'])
        
    # classify predictions as dealers or players based on top and bottom half and remove duplicates
    my_cards = set()
    deal_cards = set()
    for i in result['predictions']:
        if (i['y'] < im_height / 2):
            my_cards.add(i['class'])
        else:
            deal_cards.add(i['class'])

    print(my_cards)
    print(deal_cards)

   
    # calculate hand values
    curval = 0
    for i in my_cards:
        curval += cardVals[i[:-1]]

    dealval = 0
    for i in deal_cards:
        dealval += cardVals[i[:-1]]

    # handle ace hand over
    if (curval > 21 and ((int)('AS' in my_cards) + (int)('AH' in my_cards) + (int)('AD' in my_cards) + (int)('AC' in my_cards)) >= math.ceil((curval - 21)/10)):
        curval -= 10 * math.ceil((curval - 21)/10)
    print(curval)
    print(dealval)

    # find the best move based on the current hand
    def nextMove():        
        if (curval <= 8):
            return 0
        elif (curval >= 17):
            return 2
        else:
            print(next_move[curval - 9][dealval - 2])
            print(curval - 9)
            print(dealval - 2)
            return next_move[curval - 9][dealval - 2]
    
    # return 1 plus the move becuase you cant vibrate 0 times   
    return nextMove()+1

# start up server
while True:
    print ('Waiting for connection')
    tcpCliSock,addr = tcpSerSock.accept()
    print ('...connected from :', addr)
    try:
        # send back the next move to the client once the client sends the getmove request
        data = tcpCliSock.recv(BUFSIZE)
        data=jpysocket.jpydecode(data)
        # encode with jpyencode so that the java client can understand what is sent
        msgsend=jpysocket.jpyencode(str(get_next_move()))
        tcpCliSock.send(msgsend)        
    except KeyboardInterrupt:
        break
tcpSerSock.close()





