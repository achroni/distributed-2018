#!/usr/bin/python           # This is client.py file
import sys
import socket               # Import socket module
import datetime
import time
import select
import ast
import os.path
import threading
from operator import itemgetter

# 0 = undeliverable
# 1 = deliverable

def timesplit(timestr):
	t = timestr.split(":")
	minutes = float(t[1])
	sec = minutes * 60
	seconds = float(t[2]) +sec
	return seconds

def TimeLogPrinter(action,msg,destPort,time, time_log_file):
	time_log_file.flush()
	msg = msg.split()
	if action == "SEND":
		out = "I send {} to {} at {}".format(msg[0],destPort,time)
	else:
		out = "I receive {} from {} at {}".format(msg[0],destPort,time)
	time_log_file.write(out)
	time_log_file.write("\n")

# Validated Sequence replace Suggested Sequence in HoldBackQueue  
def modifyHoldBackQueue(queue,counter,idSender,SeqVal,idVal):
	modifyTuple = [item for item in queue if (item[1] == counter and item[2] == idSender)]
	if modifyTuple != []:
		tu = modifyTuple[0]
		for mdf in modifyTuple:
			queue.remove(mdf)
		cp = (tu[0],tu[1],tu[2],SeqVal,idVal,1)
		queue.append(cp)

# Send Validate Sequence Number to group's members
#  msg = [counter,myId,SeqVal,idVa]
def SendValidateSeqNum(counter,id,SeqVal,idVal,groupName,myport,num_messages_send):
	out = str(counter) + "ValidateSeq" + str(id) + "ValidateSeq" +str(SeqVal) + "ValidateSeq" + str(idVal) +"ValidateSeq" +groupName
	for i in mlist:
		num_messages_send = num_messages_send +1
		sock.sendto(out,i)
	return num_messages_send


# Send [msg myCounter myId] in order to request suggested sequence numbers from group's members
# Ay3anw to myCounter  prin tin kalesw 
def SendRequestForSeqNum(msg,mlist,sock,groupName,timestamp,myId,myCounter,myport,ListSeqNum,num_messages_send):
	if isInTimestamp(groupName):
		
		ListSeqNum[myCounter] = []
		out = msg + "SuggestSeq1" + str(myCounter) + "SuggestSeq1" + str(myId) + "SuggestSeq1" + groupName
		for i in mlist:
			num_messages_send = num_messages_send +1
			time_sending = datetime.datetime.now()
			time_counter = timesplit(str(time_sending)) 
			TimeLogPrinter("SEND",msg,i[1],time_counter, SendingTimeFile)
			sock.sendto(out,i)
	else:
		print "You try to write in group which you didnt join"
	return num_messages_send

# This function called after adding or replacing in HoldBackQueue
def AfterUpdateHoldBackQueue(queue,timestamp,groupName,infoSenders,bufferqueue,readfromfile,time_last_receive):
	flag = False
	queue.sort(key=lambda element: element[3])			# HoldBackQueue ordered by lowest sequence number 
	j = (" ",0,0,0,0,0)
	for i in queue:										# Recognize if there are same sequence numbers
		if i[3] == j[3]:
			flag = True
			break
		j = i
	if flag:
		# There are same sequence numbers
		queue.sort(key=lambda element: element[5])		# HoldBackQueue ordered by lowest number (first undeliverable msgs)
		
	first = queue[0]
	while first[5] == 1:								
		# while head = deliverable continue
		time_last_receive = checkFIFO(first[0],timestamp,first[1],groupName,infoSenders,first[2],bufferqueue,first[3],readfromfile,time_last_receive)
		queue.remove(first)
		if len(queue) == 0:
			break
		else:
			first = queue[0]
	return time_last_receive

# Check if Fifo condition is valid
def checkFIFO(msg,timestamp,no,groupName,infoSenders,idSender,bufferQueue,SeqVal,readfromfile,time_last_receive):
	t = timestamp[groupName]
	if t[idSender] + 1 == no :
		t[idSender] = t[idSender] + 1 
		info = infoSenders[idSender]
		time_last_receive = datetime.datetime.now()
		time_counter = timesplit(str(time_last_receive)) 
		TimeLogPrinter("RECEIVE",msg,info[1],time_counter, ReceivingTimeFile)
		sys.stdout.write("\n in {} {} says:: ".format(groupName,info[0]))
		print msg
		checkBufferQueue(timestamp,bufferQueue)
		if not readfromfile:
			sys.stdout.write('[{}]> '.format(username))
			sys.stdout.flush()
	else :
		# print "added in buffer: ", msg
		bufferQueue.append((groupName,idSender,no,msg))
	return time_last_receive

def isInTimestamp(groupName):
	for t in timestamp.keys():
		if t == groupName:
			return True
	return False

# find from port the id of sender 
def findID(port,senders):
	for k,v in senders.items():
		if int(v[1]) == port:
			return k
	return False

def checkBufferQueue(timestamp,queue):
	for q in queue:
		t = timestamp[q[0]]
		if t[q[1]] + 1 == q[2]:
			print q[0]
			print q[3]
			queue.remove(q)

def addNewGroupTimestamp(timestamp,strGroup,listIDgroup):
	timestamp[strGroup]={}
	t = timestamp[strGroup]
	for i in listIDgroup:
		t[i] = 0

def readInput():
	inp = sys.stdin.readline()
	leng = len(inp)
	leng = leng -1
	inp = inp[0:leng]
	return inp

def checkCommand (command):
	words = command.split()
	if command[0:3] == "!lg":
		return True
	elif command[0:3] == "!lm" and len(words)==2:
		return True
	elif (command[0:2]=="!j" or command[0:2] == "!e" or command[0:2] == "!w") and len(words)==2:
		return True
	elif command[0:2] == "!q":
		return True
	elif command[0:2] == "!t":
		return True
	
	else:
		return False

def updateTimestamp(timestamp,strGroup,newid):
	t = timestamp[strGroup]
	t[newid] = 0

def removeMlist(idRemove):
	info = infoSenders[idRemove]
	port = int(info[1])
	ip = info[2]
	for p in mlist:
		if p[1] == port:
			mlist.remove((ip,port))

def quitValidation(idQuit):
	if idQuit in infoSenders:
		info = infoSenders[idQuit]
		port = int(info[1])
		ip = info[2]
		del infoSenders[idQuit]
		for k,v in timestamp.items():
			if idQuit in v:
				del v[idQuit]
		if (ip,port) in mlist:
			mlist.remove((ip,port))


# Global values
flagQuit = False
bufferQueue = []	# buffer messages 
timestamp = {}		# groups' timestamps
infoSenders = {}	# info on participating groups' members
groupWrite = " "	# group's name which i write (every moment i can write to only one group)
mlist = []			# member's list of group which i write 
filescript_flag = False #flag used when there is typing from file
content = []
readfromfile = False


# Total Ordering Values
HoldBackQueue = []
ListSeqNum = {} 	# ={counter:[(SeqNum,id),..],..}
myCounter = 0
mySequence = 0


# Time - Metriseis

flag_first_send = False
time_last_receive = datetime.datetime.now()
num_messages_recv = 0
num_messages_send = 0


print 'Give me your username:'
username = readInput()
print 'Give me your UDP port:'
myport = readInput()


# UDP socket
UDP_IP = socket.gethostbyname(socket.gethostname())	 # my IP
UDP_PORT = int(myport)
UDPs = socket.socket(socket.AF_INET,socket.SOCK_DGRAM) 
UDPs.bind((UDP_IP, UDP_PORT))
print "Bind success"
print '{} {}'.format( UDP_IP, UDP_PORT)

# Files for results
SendingTimeFile = open("SendingTimeFile"+str(UDP_PORT)+".txt","w+")
SendingTimeFile.write("opened\n")

ReceivingTimeFile = open("ReceivingTimeFile"+str(UDP_PORT)+".txt","w+")
ReceivingTimeFile.write("opened\n")


# tcp socket
s = socket.socket()         	# Create a socket object

portServer = 12345                # Reserve a port for your service.
PORT_SERVER = portServer
SERVER_NAME = 'distrib-1'
UDP_SERVER_PORT = 12346

# register(ip,port,username) -> id
s.connect((SERVER_NAME, portServer))

out = "{}antepia".format(username)
command = "register " + myport 
out += command
s.send(out)

myid = s.recv(1024)				# get myid
s.close     

myId = int(myid)


socket_list = [sys.stdin, UDPs]

sys.stdout.write('[{}]> '.format(username))
sys.stdout.flush()

while True:
	
	ready_to_read,ready_to_write,in_error = select.select(socket_list , [], [])
	
	for sock in ready_to_read:

		if sock == UDPs:
			# incoming message from UDP socket
			data, addr = sock.recvfrom(1024)	# receive msg 

			if "##Server##askedYouareDead?" in data:
				# Is a message from server in order to check if I am alive
				# print "Server send me with addr {}".format(addr)
				num_messages_recv = num_messages_recv +1
				num_messages_send = num_messages_send +1
				UDPs.sendto("###YeaIamAlive###",addr)

			elif "ValidateSeq" in data:
				# Is a message in order to inform me about validated sequence
				num_messages_recv = num_messages_recv +1
				msg = data.split("ValidateSeq")
				counter = int(msg[0])
				idSender = int(msg[1])
				SeqVal = int(msg[2])
				idVal = int(msg[3])
				groupName = msg[4]
				mySequence = max (mySequence,SeqVal)										# Validated Sequence replace mySequence 
				modifyHoldBackQueue(HoldBackQueue,counter,idSender,SeqVal,idVal)
				if HoldBackQueue != []:
					# update holdbackqueue about Validate Seq
					time_last_receive = AfterUpdateHoldBackQueue(HoldBackQueue,timestamp,groupName,infoSenders,bufferQueue,readfromfile,time_last_receive)	# print deliverable messages 

			elif "SuggestSeq2" in data:
				# Is a message (from group's members) in order to inform me about members' suggested sequence
				num_messages_recv = num_messages_recv +1
				msg = data.split("SuggestSeq2")
				counter = int(msg[0])
				seq = int(msg[1])
				idSender = int(msg[2])
				groupName = msg[3]
				ListSeqNum[counter].append((seq,idSender))
				if len(ListSeqNum[counter]) >=  len(mlist) :
					# if i receive from all group's members
					Val = max(ListSeqNum[counter],key=itemgetter(0))			# Validated Sequence is max of suggested sequences
					del ListSeqNum[counter]
					num_messages_send = SendValidateSeqNum(counter,myId,Val[0],Val[1],groupName,UDP_PORT,num_messages_send)	# Send to all group's members the Validated Sequence

			elif "SuggestSeq1" in data:
				# Is a message in order to inform me about new message 
				# and to request me my suggested sequence
				num_messages_recv = num_messages_recv +1
				listOfMsg = data.split("SuggestSeq1")
				msg = listOfMsg[0]
				counter = int(listOfMsg[1])
				idSender = int(listOfMsg[2])
				groupName = listOfMsg[3]
				mySequence = mySequence +1
				info = infoSenders[idSender]
				ipaddress = info[2]
				port = int(info[1])
				out = str(counter) +"SuggestSeq2" + str(mySequence) + "SuggestSeq2" +str(myId) + "SuggestSeq2" +groupName
				num_messages_send = num_messages_send +1
				UDPs.sendto(out,(ipaddress,port))								# send my suggested sequence
				HoldBackQueue.append((msg,counter,idSender,mySequence,myId,0)) 	# put in HoldBackQueue the undeliverable message
				time_last_receive = AfterUpdateHoldBackQueue(HoldBackQueue,timestamp,groupName,infoSenders,bufferQueue,readfromfile,time_last_receive)	# check about deliverable messages and print

			elif "##Quit##" in data:
				# Is a message (from Server) in order to inform me that 
				# someone quited
				num_messages_recv = num_messages_recv +1
				msg = data.split()
				idQuit = int(msg[1])
				quitValidation(idQuit)			# remove from all groups

			elif "##Timestamp##" in data:
				# Is a message (from group's members) in order to initialize 
				# correct timestamp of this group 
				num_messages_recv = num_messages_recv +1
				msg = data.split("##Timestamp##")
				idOldMember = int(msg[0])
				tOldMember = int (msg[1])
				groupName = msg[2]
				t = timestamp[groupName]
				t[idOldMember] = tOldMember

			elif "##remove##" in data:
				# Is a message (from Server) in order to inform me that 
				# someone exited from this group
				num_messages_recv = num_messages_recv +1
				msg = data.split("##remove##")
				idRemove = int(msg[0])
				groupName = msg[1]
				t = timestamp[groupName]
				del t[idRemove]
				if groupName == groupWrite:
					removeMlist(idRemove)

			elif addr[1] == UDP_SERVER_PORT:
				# Is a message from server in order to 
				# inform me that someone joined in this group
				num_messages_recv = num_messages_recv +1
				newEntry = data.split(":")
				newId = int(newEntry[0])
				groupName = newEntry[1]
				newInfo =  ast.literal_eval(newEntry[2])
				infoSenders[newId] = newInfo
				updateTimestamp(timestamp,groupName,newId)
				if groupName == groupWrite:
					mlist.append((newInfo[2],int(newInfo[1])))
				# send to new member my timestamp 
				t = timestamp[groupName]
				m = "{}##Timestamp##{}##Timestamp##{}".format(myid,t[myId],groupName)
				num_messages_send = num_messages_send +1
				UDPs.sendto(m,(newInfo[2],int(newInfo[1])))

			elif not data :
			    print '\nDisconnected from chat server'
			    sys.exit()

			else :
				# It will never run!!!
				print "Error !!! "

		else:
			# typed command or message
			
			sys.stdout.flush()						# print [username]>
			command = sys.stdin.readline()	
		
			if command[0] == '!':
				# is command
				if checkCommand(command):
					# tcp connection
					s = socket.socket()         	# Create a socket object
					portServer = PORT_SERVER 
					s.connect((SERVER_NAME, portServer))
					out = myid + "antepia" +command
					s.send(out)
					
					words = command.split() 
					if command[0:3] == "!lg" or command[0:3] == "!lm":
						print s.recv(1024)			# print server's answer
						s.close 					# Close the socket when done

					elif command[0:2] == "!j":
						olokliro = s.recv(4096)
						miso = olokliro.split("##Server##Join")
						idList = miso[0]						# receive list of members' ids
						msgServer = miso[1]					# receive dictionary of members' username,
						newdict = ast.literal_eval(msgServer)		# ip address and UDP port
						infoSenders.update(newdict)
						listOfIds = ast.literal_eval(idList)
						addNewGroupTimestamp(timestamp,words[1],listOfIds)	# create group's timestamp
						s.close									# Close the socket when done
					
					elif command[0:2] == "!w":
						groupWrite = words[1]
						msgServer = s.recv(1024)			# receive mlist (list of tuples(ip address,port))
						mlist = ast.literal_eval(msgServer)
						if mlist == False:
							print "Wrong Group!!!"

					elif command[0:2] == "!e":
						del timestamp[words[1]]			# deleted group's timestamp
						if words[1] == groupWrite:	
							mlist = []

					elif command[0:2] == "!t":
						filename = words[1]
						if mlist == []:
							print "No group to message to!"
						elif os.path.isfile(filename):
							with open(filename, 'r') as f:
								content = f.readlines()
								content = [x.strip() for x in content]
								filescript_flag = True
								readfromfile = True
						else: 
							print "No such file found.\nPlease try again!"
					else :
						s.close 
						print 'Exiting...'
						print "Num Of messages which Send: {}".format(num_messages_send)
						print "Num Of messages which Receive: {}".format(num_messages_recv)
						throughput = time_last_receive - begin_time
						print "Total Time Send and Receive: {}".format(throughput)
						flagQuit = True
						break
				else:
					print "Wrong command"

			else:
				# user typed a message
				msg = command
				l = len(msg) - 1
				msg = msg[0:l]
				myCounter = myCounter +1
				num_messages_send = SendRequestForSeqNum(msg,mlist,UDPs,groupWrite,timestamp,myId,myCounter,UDP_PORT,ListSeqNum,num_messages_send)
			
			if not readfromfile:
				sys.stdout.write('[{}]> '.format(username))
				sys.stdout.flush()

# to filescript_flag einai ena flag pou einai valid gia oso typwnoyme apo arxeio. Arxikopoieitai se True apo thn entolh 
# !t filename kai ginetai False otan teleiwsei na typwnei apo to arxeio. Oso einai True typvnei grammh grammh. Ta noumera sthn
# arxh ta 8eloume gia na blepoume an ginetai swsta to total ordering

	if filescript_flag:
		if content == [] :
			filescript_flag = False
			readfromfile = False
		else:
			msg = content.pop(0)
			l = len(msg)
			msg = msg[0:l]
			myCounter = myCounter +1
			
			if flag_first_send == False:
				flag_first_send = True
				begin_time = datetime.datetime.now()

			num_messages_send = SendRequestForSeqNum(msg,mlist,UDPs,groupWrite,timestamp,myId,myCounter,UDP_PORT,ListSeqNum,num_messages_send)
			
	
	if (flagQuit == True):
		SendingTimeFile.close()
		ReceivingTimeFile.close()
		break
