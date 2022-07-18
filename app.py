import threading
from typing import Union
import av
import numpy as np
import streamlit as st
import random
import HandTrackingModule as htm
import time
import pandas as pd
import requests
import io
from PIL import Image

import sqlite3
#databases connections
conn=sqlite3.connect('database.db')
c=conn.cursor()

from streamlit_webrtc import(
    RTCConfiguration,
    WebRtcMode,
    WebRtcStreamerContext,
    webrtc_streamer,
    VideoTransformerBase)
RTC_CONFIGURATION = RTCConfiguration({"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]})


def create_table():
    c.execute('CREATE TABLE IF NOT EXISTS userstable(username TEXT PRIMARY KEY,score TEXT)')

def drop_all_tables():
    c.execute("DROP TABLE userstable")

def add_data():
    c.execute('INSERT OR IGNORE INTO userstable(username,score) VALUES (?,?)',("player","0"))
    c.execute('INSERT OR IGNORE INTO userstable(username,score) VALUES (?,?)',("computer","0"))
    c.execute('INSERT OR IGNORE INTO userstable(username,score) VALUES (?,?)',("next_player_bat","False"))
    conn.commit()

def update_scores(username,score):
    c.execute('UPDATE userstable SET score =? WHERE username =?',(score,username))
    conn.commit()

def get_score(username):
    c.execute('SELECT (score) FROM userstable WHERE username =?',(username,))
    data=c.fetchall()
    return data

def main():
    class VideoTransformer(VideoTransformerBase):
        frame_lock: threading.Lock  # `transform()` is running in another thread, then a lock object is used here for thread-safety.
        out_image: Union[np.ndarray, None]

        def __init__(self) -> None:
            self.frame_lock = threading.Lock()
            self.out_image = None

        def transform(self, frame: av.VideoFrame) -> np.ndarray:
            in_image = frame.to_ndarray(format="bgr24")

            out_image = in_image[:, ::-1, :]

            with self.frame_lock:
                self.in_image = in_image

            return in_image

    ctx = webrtc_streamer(key="snapshot", 
            mode=WebRtcMode.SENDRECV,
            rtc_configuration=RTC_CONFIGURATION,
            media_stream_constraints={"video": True, "audio": False},
            async_processing=True,
            video_transformer_factory=VideoTransformer)
    
    detector=htm.handDetector(detectionCon=1)
    create_table()
    add_data()
    #next_player_bat=False
    if ctx.video_transformer:
        
        if st.button("Capture"):
            with ctx.video_transformer.frame_lock:
                out_image = ctx.video_transformer.in_image
                #out_image = ctx.video_transformer.out_image
                out_image = out_image.astype(np.uint8)
            if out_image is not None:
                #st.write("Output image:")
                #st.image(out_image, channels="BGR")
                img=detector.findHands(out_image)
                fingersList=detector.findPosition(img,draw = True)
                value = processing(fingersList)
                player_value=value[0]
                computer_value=value[1]



                player_value_col,computer_value_col=st.columns(2)
                player_value_col.info("Player value: "+str(player_value))
                computer_value_col.info("computer value: "+str(computer_value))

                player_value_pic_col,computer_value_pic_col=st.columns(2)
                notation_display(player_value_pic_col,player_value)
                notation_display(computer_value_pic_col,computer_value)

                data=get_score("next_player_bat")
                lo=modification(data)
                next_player_bat=str(' '.join(lo))


                if player_value!= computer_value and next_player_bat== "False":
                    if player_value !=0 and computer_value!=0:
                        data=get_score("player")
                        lo=modification(data)
                        player_score_str=str(' '.join(lo))
                        player_score=int(player_score_str)
                        player_score+=player_value
                        update_scores("player",str(player_score))



                elif player_value!=computer_value and next_player_bat=="True":
                    if player_value !=0 and computer_value!=0:
                        data=get_score("computer")
                        lo=modification(data)
                        comp_score_str=str(' '.join(lo))
                        comp_score=int(comp_score_str)
                        comp_score+=computer_value
                        update_scores("computer",str(comp_score))

                        data=get_score("player")
                        lo=modification(data)
                        player_score_str=str(' '.join(lo))
                        player_score=int(player_score_str)

                        if comp_score>player_score:
                            st.info(" COMPUTER WON THE MATCH..... YOU LOST THE GAME.......")
                            #next_player_bat= False
                            drop_all_tables()
                            create_table()
                            add_data()


                elif player_value == computer_value and next_player_bat=="False":
                    if player_value !=0 and computer_value!=0:
                        st.info("player(batsmen) is out...............")
                        #next_player_bat=True
                        update_scores("next_player_bat","True")

                elif player_value == computer_value and next_player_bat=="True":
                    if player_value !=0 and computer_value!=0:
                        st.warning(" G A M E    O V E R")
                        data=get_score("player")
                        lo=modification(data)
                        player_score_str=str(' '.join(lo))
                        player_score=int(player_score_str)

                        data1=get_score("computer")
                        lo=modification(data1)
                        comp_score_str=str(' '.join(lo))
                        comp_score=int(comp_score_str)

                        player_score_col.info("Player Score: "+str(player_score))
                        comp_score_col.info("Computer Score: "+str(comp_score))
                        if player_score>comp_score:
                            st.success(" YOU WON THE MATCH....")
                        else:
                            st.info(" COMPUTER WON THE MATCH..... YOU LOST THE GAME.......")

                        #next_player_bat= False

                        drop_all_tables()
                        create_table()
                        add_data()

                player_score_col,comp_score_col=st.columns(2)

                data=get_score("player")
                lo=modification(data)
                player_score_str=str(' '.join(lo))
                player_score=int(player_score_str)

                data=get_score("computer")
                lo=modification(data)
                comp_score_str=str(' '.join(lo))
                comp_score=int(comp_score_str)

                player_score_col.info("Player Score: "+str(player_score))
                comp_score_col.info("Computer Score: "+str(comp_score))

            else:
                st.warning("No frames available yet.")
    if st.button("STOP GAME"):
            drop_all_tables()
            create_table()
            add_data()    
                


    menu=["What is this Game","Instructions"]
    choice=st.selectbox("Menu",menu)
    if choice=="Instructions":
        col1,col2,col3=st.columns(3)
        notation_display(col1,1)
        notation_display(col2,2)
        notation_display(col3,3)

        col4,col5,col6=st.columns(3)
        notation_display(col4,4)
        notation_display(col5,5)
        notation_display(col6,6)

        st.info("NOTE: Use these notations for their Respective Value.")

        st.text("Instructions:"
                +"\n1. Use 'Start' button for starting the game."
                +"\n2. Use 'Capture' button for accepting your hand notations."
                +"\n3. Use 'Stop' button for quitting the game."
                +"\n4. Use Left hand for showing the notations in the game.")
    elif choice=="What is this Game":
        st.header("Hand Cricket:")
        st.subheader("Hand Cricket is a game in which two players show number value on their respective fingers using hand notations."
                    +"If the number values are equal, then the batsmen is declared out."
                    +"Else, the value is added to the batsmen team score and considered the value as runs of the batting team.")
        col1,col2,col3=st.columns(3)
        url_image_loader(col2,"https://i.imgur.com/PXHR2fC.jpg")



def processing(fingersList):
    fingerTipIds=[4,8,12,16,20]
    if len(fingersList)!=0:
        fingers=[]

        # for thumb finger only
        if fingersList[fingerTipIds[0]][1] < fingersList[fingerTipIds[0] - 1][1]:
            fingers.append(1)
        else:
            fingers.append(0)

        for id in range(1, 5):
            if fingersList[fingerTipIds[id]][2] < fingersList[fingerTipIds[id] - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)
        #######calculation for hand cricket############################################################################
        value = 0
        # conditions for 0
        if fingers[0] == 0 and fingers[1] == 0 and fingers[2] == 0 and fingers[3] == 0 and fingers[4] == 0:
            value = 0
            compValue=0
        # conditions for 1
        if fingers[0] == 0 and fingers[1] == 1 and fingers[2] == 0 and fingers[3] == 0 and fingers[4] == 0:
            value = 1
        # condition for 2
        elif fingers[0] == 0 and fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0 and fingers[4] == 0:
            value = 2
        # condition for 3
        elif fingers[0] == 0 and fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1 and fingers[4] == 0:
            value = 3
        # condition for 4
        elif fingers[0] == 0 and fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1 and fingers[4] == 1:
            value = 4
        # condition for 5
        elif fingers[0] == 1 and fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1 and fingers[4] == 1:
            value = 5
        # condition for 6
        elif fingers[0] == 1 and fingers[1] == 0 and fingers[2] == 0 and fingers[3] == 0 and fingers[4] == 0:
            value = 6
        else:
            value=0
            compValue=0

        if value!=0:
            compValue = random.randint(1, 6)

        return value,compValue

    elif(len(fingersList)==0):
        value=0
        compValue=0
        return value,compValue

def url_image_loader(colname,url):
    response = requests.get(url)
    image_bytes = io.BytesIO(response.content)
    img = Image.open(image_bytes)
    colname.image(img)


def notation_display(colname,value):
    if value ==0:
        url_image_loader(colname,"https://i.imgur.com/UykhSw4.jpg")
    elif value ==1:
        url_image_loader(colname,"https://i.imgur.com/cXdXnCJ.jpg")
    elif value==2:
        url_image_loader(colname,"https://i.imgur.com/irEy9Y3.jpg")
    elif value==3:
        url_image_loader(colname,"https://i.imgur.com/sElkHu3.jpg")
    elif value==4:
        url_image_loader(colname,"https://i.imgur.com/5glH11B.jpg")
    elif value==5:
        url_image_loader(colname,"https://i.imgur.com/cBQscdP.jpg")
    elif value==6:
        url_image_loader(colname,"https://i.imgur.com/01vJJh5.jpg")

def modification(t):
    te = ""
    for i in t:
        for j in i:
            te = te + j + ","

    lo = te.split(",")
    lo.remove("")
    return (lo)

if __name__ == "__main__":
    main()