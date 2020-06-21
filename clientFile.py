#!/usr/bin/python           # This is client.py file
import sys
import socket               # Import socket module
import time
import select
import ast
import os.path
import datetime


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
	# time_log_file.write(str(time))
	time_log_file.write("\n")


def mysplit (msg , split_str):
	splitted_msg = msg.split(split_str)
	ret_split_msg = [splitted_msg[0], splitted_msg[1], ''.join(splitted_msg[2:])]
	return ret_split_msg

# send to all memebers of groupName
def sendBroadcast (msg,mlist,sock,groupName,timestamp,myId,myNumber,num_messages_send):
	if isInTimestamp(groupName):
		time_counter = datetime.datetime.now()
		m = str(myNumber)
		msg = m + "tsakoulis" + groupName + "tsakoulis" + msg + "tsakoulis" + str(time_counter)
		for i in mlist:
			num_messages_send = num_messages_send + 1
			sock.sendto(msg,i)
	else:
		print "You are not in this group : {}!!!".format(groupName)
	return num_messages_send

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

#def testing_thread(content,mlist,sock,groupName,timestamp,myId):
#	for x in content:
#		sendBroadcast(x,mlist,sock,groupName,timestamp,myId)

# Global values
flagQuit = False
bufferQueue = []	# buffer messages 
timestamp = {}		# groups' timestamps
infoSenders = {}	# info on participating groups' members
groupWrite = " "	# group's name which i write (every moment i can write to only one group)
mlist = []		# member's list of group which i write 
write_flag = False	#flag used when we are writing in a group if we do not want our label to be printed
filescript_flag = False #flag used when there is typing from file
content = []
myNumber = 0

# Time & metrisi
# first_send_time

flag_first_send = False
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

TimeLogfile = open("Timelogfile"+str(UDP_PORT)+".txt","w+")
TimeLogfile.write("opened\n")					

# tcp socket
s = socket.socket()         	# Create a socket object
# host = socket.gethostname() 	# Get local machine name
#portServer = 12345              # Reserve a port for your service.


portServer = 12345                # Reserve a port for your service.
PORT_SERVER = portServer
SERVER_NAME = 'distrib-1'
UDP_SERVER_PORT = 12346

# register(ip,port,username) -> id
s.connect((SERVER_NAME, portServer))
# s.send(username)
# time.sleep(1)
out = "{}antepia".format(username)
command = "register " + myport 
out += command
s.send(out)
# time.sleep(1)
myid = s.recv(1024)				# get myid
s.close     

myId = int(myid)


socket_list = [sys.stdin, UDPs]

sys.stdout.write('[{}]> '.format(username))
sys.stdout.flush()

while True:
	
	ready_to_read,ready_to_write,in_error = select.select(socket_list , [], [])
	#print ready_to_read,ready_to_write,in_error
	# print "-----------------------------"
	# print "Timestamp beginning of while: ", timestamp
	
	for sock in ready_to_read:
		#print "for sock :" , sock
		#print UDPs
		if sock == UDPs:
			# print "-----------------------------"
			# print "Message from UDP socket"
			
			# incoming message from UDP socket
			data, addr = sock.recvfrom(1024)	# receive msg 
			
#			print "Receive from: ", addr, "data: ", data
			if "##Server##askedYouareDead?" in data:
				# Is a message from server in order to check if I am alive
				# print "Server send me with addr {}".format(addr)
				num_messages_recv = num_messages_recv + 1
				num_messages_send = num_messages_send + 1
				UDPs.sendto("###YeaIamAlive###",addr)

			elif "##Quit##" in data:
				# Is a message (from Server) in order to inform me that 
				# someone quited
				num_messages_recv = num_messages_recv + 1
				msg = data.split()
				idQuit = int(msg[1])
				quitValidation(idQuit)			# remove from all groups

			elif "##Timestamp##" in data:
				# Is a message (from group's members) in order to initialize 
				# correct timestamp of this group 
				num_messages_recv = num_messages_recv + 1
				msg = data.split("##Timestamp##")
				idOldMember = int(msg[0])
				tOldMember = int (msg[1])
				groupName = msg[2]
				t = timestamp[groupName]
				t[idOldMember] = tOldMember

			elif "##remove##" in data:
				# Is a message (from Server) in order to inform me that 
				# someone exited from this group
				num_messages_recv = num_messages_recv + 1
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
				num_messages_recv = num_messages_recv + 1
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
				num_messages_send = num_messages_send + 1
				UDPs.sendto(m,(newInfo[2],int(newInfo[1])))

			elif not data :
			    print '\nDisconnected from chat server'
			    sys.exit()

			else :
				# Is a message from members
				num_messages_recv = num_messages_recv + 1
				w = data.split("tsakoulis")
				no = int(w[0])
				groupName = w[1]
				msg = w[2]
				time_begin = timesplit(w[3])
				# time_begin = float(w[3])
				idSender = findID(addr[1],infoSenders)
				t = timestamp[groupName]
				if t[idSender] + 1 == no :
					# validate fifo's condition
					t[idSender] = t[idSender] + 1 
					info = infoSenders[idSender]
					time_last_receive = datetime.datetime.now()
					time_counter = timesplit(str(time_last_receive)) - time_begin
					# print "TIME : Time counter is now: " + str(time_counter)
					TimeLogPrinter("RECEIVE",msg,info[1],time_counter, TimeLogfile)
					sys.stdout.write("\n >> in {} {} says:: ".format(groupName,info[0]))
					print msg
					checkBufferQueue(timestamp,bufferQueue)
				else :
					print "added in buffer: ", msg
					bufferQueue.append((groupName,idSender,no,msg))	#this msg is added to BufferQueue 
				
				sys.stdout.write('[{}]> '.format(username))
				sys.stdout.flush()

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
						s.close 									# Close the socket when done
					
					elif command[0:2] == "!w":
						groupWrite = words[1]
						msgServer = s.recv(1024)			# receive mlist (list of tuples(ip address,port))
						mlist = ast.literal_eval(msgServer)
						write_flag = True
						if mlist == False:
							print "Wrong Group!!!"

					elif command[0:2] == "!e":
						del timestamp[words[1]]			# deleted group's timestamp
						write_flag = False

						if words[1] == groupWrite:	
							mlist = []

					elif command[0:2] == "!t":
						filename = words[1]
						#filename = 'long_message.txt'
						if mlist == []:
							print "No group to message to!"
						elif os.path.isfile(filename):
							with open(filename, 'r') as f:
								content = f.readlines()
								content = [x.strip() for x in content]
								filescript_flag = True
							#TODO na doume an prepei na kleisoyme to arxeio
						else: 
							print "No such file found.\nPlease try again!"
					else :
						s.close 
						print 'Exiting...'
						print "Num of messages which send {}".format(num_messages_send)
						print "Num of messages which receive: {}".format(num_messages_recv)
						througput = time_last_receive - first_send_time 
						print "Total Time Send and Receive: {}".format(througput)
						flagQuit = True
						break
				else:
					print "Wrong command"

			else:
				# user typed a message
				msg = command
				l = len(msg) - 1
				msg = msg[0:l]
				myNumber = myNumber +1
				num_messages_send = sendBroadcast(msg,mlist,UDPs,groupWrite,timestamp,myId,myNumber,num_messages_send)
			
			# if not filescript_flag:
			sys.stdout.write('[{}]> '.format(username))
			sys.stdout.flush()

# to filescript_flag einai ena flag pou einai valid gia oso typwnoyme apo arxeio. Arxikopoieitai se True apo thn entolh 
# !t filename kai ginetai False otan teleiwsei na typwnei apo to arxeio. Oso einai True typvnei grammh grammh. Ta noumera sthn
# arxh ta 8eloume gia na blepoume an ginetai swsta to total ordering

	if filescript_flag:
		if content == [] :
			filescript_flag = False
		else:
			msg = content.pop(0)
			l = len(msg)
			msg = msg[0:l]
			myNumber = myNumber +1
			if flag_first_send == False:
				flag_first_send = True
				first_send_time = datetime.datetime.now()

			num_messages_send = sendBroadcast(msg,mlist,UDPs,groupWrite,timestamp,myId,myNumber,num_messages_send)
			# time.sleep(1) # we use this so that the total ordering can be visible
				
	if (flagQuit == True):
		break
