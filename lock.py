from datetime import datetime
import RPi.GPIO as GPIO
import threading
import select
import socket
import cv2
import time
import sys
import csv
import os
GPIO.setmode(GPIO.BCM)
camera = cv2.VideoCapture(0)
camera.set(3, 320)
camera.set(4, 240)
camera_lock = threading.Lock()
class Server:
    host = ''
    port_stream = 8888
    port_control = 8889
    def __init__(self):
        self.socket_stream = None
        self.socket_control = None
        self.threads = []
    def open_socket(self):
        try:
            self.socket_stream = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            self.socket_stream.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR, 1)
            self.socket_stream.bind((self.host, self.port_stream))
            self.socket_stream.listen(5)
            self.socket_control = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_control.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket_control.bind((self.host, self.port_control))
            self.socket_control.listen(5)
            log('[INFO]', 'Server is listening on {} and {}'.format(self.port_stream, self.port_control))
        except socket.error, (value, message):
            if self.socket_stream:
                self.socket_stream.close()
            if self.socket_control:
                self.socket_control.close()
            log('[ERROR]', 'Could not open socket: ' + message)
            sys.exit(1)
    def run(self):
        self.open_socket()
        try:
            input = [self.socket_stream, self.socket_control, sys.stdin]
            running = 1
            while running:
                input_ready, output_ready, except_ready = select.select(input, [], [])
                for s in input_ready:
                    if s == self.socket_stream:
                        c = StreamClient(self.socket_stream.accept())
                        c.start()
                        self.threads.append(c)
                    elif s == self.socket_control:
                        c = ControlClient(self.socket_control.accept())
                        c.start()
                        self.threads.append(c)
                    elif s == sys.stdin:
                        cmd = sys.stdin.readline().strip()
                        if cmd == 'show':
                            s = ShowFrame()
                            s.start()
                            self.threads.append(s)
                        elif cmd == 'quit':
                            running = 0
                        elif cmd == '':
                            pass
                        else:
                            print 'Command not found: '+cmd
        except KeyboardInterrupt:
            pass
        self.socket_stream.shutdown(socket.SHUT_WR)
        self.socket_control.shutdown(socket.SHUT_WR)
        self.socket_stream.close()
        self.socket_control.close()
        for t in self.threads:
            t.running = 0
        while len(self.threads) > 0:
            self.threads = [t.join(1) for t in self.threads if t is not None and t.isAlive()]
        print 'Thank you'
        print 'If it hangs here, please press Ctrl+\\ to quit'
class StreamClient(threading.Thread):
    def __init__(self, (client, address)):
        threading.Thread.__init__(self)
        self.client = client
        self.address = address
        self.running = 1
        log(self.address, "connect")
    def run(self):
        try:
            while self.running:
                camera_lock.acquire()
                grabbed, frame = camera.read()
                camera_lock.release()
#                jpeg = cv2.imencode('.jpg', frame)[1].tostring()
#                self.client.send(jpeg)#send
        except socket.error as e:
            pass
        self.client.close()
        log(self.address, "close")
class ControlClient(threading.Thread):
    def __init__(self, (client, address)):
        threading.Thread.__init__(self)
        self.client = client
        self.address = address
        self.running = 1
        self.lock = threading.Lock()
        log(self.address, "connect")
    def run(self):
        try:
            cmd=''
            count=0
            a=[]
            recreatflag=False
            auth=False
            r=open("data.csv","r")
            aall=[]
            datacounty=0
            for ggrow in csv.reader(r):
                aall.append(ggrow)
                datacounty=datacounty+1
            r.close()
            print "Data in DataBase now!"
            print aall
            while self.running:
                if not(len(a)==0):
                    if a==['Dannie']:
                        auth=True
                cmd=''
                data=[]
                data = self.client.recv(400)
                if not data:
                    self.client.close()
                    self.running = 0

                for char in data:
                    if not(char == '\n' or char == '\r'):
                        cmd+= char
                fun='N'
                again=False
                self.lock.acquire()
                if cmd =='RebuildDataBase!'and not(len(a)==0):
                        if a[0]=='Dannie':
                            print 'Create DataBase!'
                            access=True
                            recreatflag=True
                            if not os.path.isfile('data.csv'):
                                f=open("data.csv","w")
                            else:
                                os.remove("data.csv");
                                f=open("data.csv","w")
                            f.close()
                            count=0
                            cmd=''
                            a=[]
                            print "DataBase=",a
                        else:
                            print"Deny"
                            cmd=''
                            a=[]
                elif cmd =='RebuildDataBase!'and not(len(a)==0):
                    if not(a[0]=='Dannie'):
                        print"Deny!"
                        cmd=''
                        a=[]
                elif cmd =='RebuildDataBase!'and (len(a)==0):
                    print "Please enter your name!"
                elif cmd=='0.0tI':
                    print'Reinsert again!'
                else:
                    for str in cmd:
                        if ((str=='I')and (not(cmd[0]=='I'))):#insert db
                            if auth==True:
                                fun='I'
                            else:
                                print 'You have not right to insert your data'
                                fun='N'
                                cmd=''
                                a=[]
                        elif str=='Z'and not(cmd[0]=='Z') :     #comparison
                            fun='Z'
                        else:#keep
                            fun='G'
                            again=True
                    if fun=='G'and again==True:

                        temp=''
                        if cmd[0]=='N':
                            a=[]
                            for k in range(1,len(cmd)):
                                temp+=cmd[k]
                            a.append(temp)
                        else:
                            for ss in cmd:
                                if not(ss=='t'):
                                    temp+=ss
                                else:
                                    a.append(float(temp))#node
                    elif fun=='I':
                        print 'enter I'
                        if again==False:
                            a=[]
                        temp=''
                        for ss in cmd:
                            if not(ss=='t')and not(ss=='I'):
                                temp+=ss
                            elif not(ss=='I'):
                                a.append(float(temp))
                                temp=''
                        print 'Insert data to database!'
                        r=open("data.csv","r")
                        datacount=0
                        total=[]
                        for row in csv.reader(r):# temp=''
                            total.append(row)# if cmd=='0.0tI':
                            datacount=datacount+1# a.append(5.0)
                            #                       count=0
                        print 'Database(before)=',total# cmd=''
                        f=open("data.csv","w")# temp+=cc
                        total.append(a)# count=1
                        wdata=csv.writer(f)# elif count==1:
                        wdata.writerows(total)# temp=''
                        print 'Database(after)=',total
                        f.close()# for cc in cmd:
                        r.close()#                          if not(cc=='t')and not(cc=='I'):
                        r=open("data.csv","r")
                        datacount=0
                        all=[]
                        for grow in csv.reader(r):
                            all.append(grow)
                            datacount=datacount+1
                        r.close()

                    elif fun=='Z':
                        if again==False:
                            a=[]
                        temp=''
                        for ss in cmd:
                            if not(ss=='t')and not(ss=='I'):
                                temp+=ss
                            elif not(ss=='I'):
                                a.append(float(temp))
                                temp=''
                        rdata=open("data.csv","r")
                        check=False
                        correctdata=[]
                        datanum=0
                        for row in csv.reader(rdata):
                            datanum=datanum+1
                            if len(a)==len(row):
                                for i in range(1,len(row)):
                                    if not(a[i]>=float(row[i])*0.2 and a[i]<=float(row[i])*1.8)or not(a[0]==row[0]):# temp+=cc
                                        check=False# else:
                                        break
                                    else:# print'temp=', temp
                                        check=True# a.append(float(temp))
                                        correctdata.append(float(row[i]))#
                            if check==True:
                                print"Match %dth data!" %(datanum)
                                for i in range(1,len(correctdata)):
                                    print "Your code: %f Original code: %f"%(a[i],correctdata[i])# datacount=0
                                StepPins = [17,22,23,24]
                                for pin in StepPins:
                                   # print "Setup pins"
                                    GPIO.setup(pin,GPIO.OUT)
                                    GPIO.output(pin, False)

# Define advanced sequence
# as shown in manufacturers datasheet
                                Seq = [[1,0,0,1],
                                       [1,0,0,0],
                                       [1,1,0,0],
                                       [0,1,0,0],
                                       [0,1,1,0],
                                       [0,0,1,0],
                                       [0,0,1,1],
                                       [0,0,0,1]]

                                StepCount = len(Seq)
                                StepDir = 2 # Set to 1 or 2 for clockwise
            # Set to -1 or -2 for anti-clockwise

# Read wait time from command line
                                if len(sys.argv)>1:
                                    WaitTime = int(sys.argv[1])/float(1000)
                                else:
                                    WaitTime = 10/float(1000)

# Initialise variables
                                StepCounter = 0
                                c=0
# Start main loop
                                while True:
                                    c=c+1
                                    print StepCounter,
                                    print Seq[StepCounter]

                                    for pin in range(0,4):
                                        xpin=StepPins[pin]# Get GPIO
                                        if Seq[StepCounter][pin]!=0:
 #                                          print " Enable GPIO %i" %(xpin)
                                            GPIO.output(xpin, True)
                                        else:
                                            GPIO.output(xpin, False)

                                    StepCounter += StepDir

  # If we reach the end of the sequence
  # start again
                                    if (StepCounter>=StepCount):
                                        StepCounter = 0
                                    if (StepCounter<0):
                                        StepCounter = StepCount+StepDir

  # Wait before moving on
                                    time.sleep(WaitTime)#715-2down 687--2up
#                                   print c, '------------------------'
                                    if c==715 and StepDir==2:
                                        time.sleep(5)
                                        c=0
                                        StepDir=-2
                                    elif c==587 and StepDir==-2:
                                        break



                                break#                      total=[]
                        if check==False:
                                print'Mismatch!'
                self.lock.release()
        except socket.error as e:
            pass
        self.client.close()
        log(self.address, "close")
def log(ip, msg):
    print datetime.today().strftime('%b %d %H:%M:%S'),
    print "{} {}.".format(ip, msg)
if __name__ == '__main__':
    s = Server()
    s.run()


camera.release()
GPIO.cleanup()
