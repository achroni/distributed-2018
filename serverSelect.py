#!/usr/bin/python           # This is server.py file

import socket               # Import socket module
import select
import time

# Quit from app
def quit(id):
	for k in groups.keys():
		removeFromGroup(id,k)	
	del ids[id]			

# Print name of Groups groups: [..]
def printGroups():
	out = ""
	flag = True
	out +='groups: '
	for k in groups.keys():
		if flag == False:
			out +=', '
		else:
			flag = False
		out += '[{}]'.format(k)
	return out

# Print members of Group with name = strGroup , memebers: (..)
def printMemebersOf(strGroup):
	out= ""
	flag = True
	out += 'members: '
	for k, v in groups.items():
		if k == strGroup:
			for i in v:
				if flag == False:
					out += ', '
				else:
					flag = False
				my = ids[i]
				out += '({})'.format(my[0])
	return out

# Return true if there is strGroup 
def findGroup(strGroup):
	find = False
	for k in groups.keys():
		if (k == strGroup):
			find = True
	return find

# User with id join group with name strGroup
def insertGroup(id,strGroup):
	if findGroup(strGroup):
		if not(findMemberInGroup(id,strGroup)):
			groups[strGroup].append(id)
	else:
		groups[strGroup] = [id]

# Return true if there is memeber with this id in strGroup
def findMemberInGroup(id,strGroup):
	findGroup = False
	find = False
	for k, v in groups.items():
		if (k == strGroup):
			findGroup = True
			for i in v:
				if i == id:
					find = True
	if not(findGroup):
		print "Den uparxei tetoio Group!"
	return find	

# Return true if this strGroup dont have members
def emptyGroup(strGroup):
	empty = True
	for k, v in groups.items():
		if (k == strGroup):
			for i in v:
				empty = False
	return empty

# Delete the member with this id from strGroup
def removeFromGroup(id,strGroup):
	if findMemberInGroup(id,strGroup):
		groups[strGroup].remove(id)
		if emptyGroup(strGroup):
			del groups[strGroup]
	else:
		print "Den uparxei tetoio melos!"

# Add in ids dictionary the tuple (strUser,..) with key i and return the key
def register(strUser,intPort,ipAddr): 
	if len(ids) == 0:
		i =0 
	else:
		i = ids.keys()[-1] + 1

	ids[i] = (strUser,intPort,ipAddr)
	return i

def sendInfoMembersOf(strGroup):
	flag = True
	out = "{ "
	idList = groups[strGroup]
	for i in idList:
		if flag == False:
			out += ', '
		else:
			flag = False
		out += "{}:".format(i)
		out += " {}".format(ids[i])
	out += " }"
	return out

def sendMemberListOf(strGroup):
	flag = True
	out = "["
	listId = groups[strGroup]
	for i in listId:
		info = ids[i]
		if flag == False:
			out += ', '
		else:
			flag = False
		out += "('{}',{})".format(info[2],info[1])
	out += "]"
	return out

def sendToOldMembers(listIds,id,groupName,socket):
	for i in listIds:
		info = ids[i]
		port = int(info[1])
		ipAddr = info[2]
		infoNewMember = ids[id]
		msg = "{}:{}:".format(id,groupName)
		msg += str(infoNewMember)
		socket.sendto(msg,(ipAddr,port))

def sendRemovingMember(listIds,id,groupName,socket):
	for i in listIds:
		info = ids[i]
		port = int(info[1])
		ipAddr = info[2]
		msg = "{}##remove##{}".format(id,groupName)
		socket.sendto(msg,(ipAddr,port))


def sendQuitingMember(id,socket):
	for k,v in ids.items():
		ipAddr = v[2]
		port = int(v[1])
		msg = "##Quit## {}".format(id)
		socket.sendto(msg,(ipAddr,port))


def checkDeadClients(socket,ids,groups):
	for k,v in ids.items():
		ipAddr = v[2]
		port = int(v[1])
		socket.sendto("##Server##askedYouareDead?",(ipAddr,port))
		timeout = 1
		socket_list = [socket]
		ready_to_read,ready_to_write,in_error = select.select(socket_list , [], [],timeout)
		if not ready_to_read:
			print "Client with id = {} is dead!".format(k)
			quit(k)
			sendQuitingMember(k,socket)
		else:
			for sock in ready_to_read:
				if sock == socket:
					data, addr = sock.recvfrom(1024)	# receive msg
					if "###YeaIamAlive###" in data:
						print "Client {} is Alive".format(addr) 

groups = {}	# = {groupname:[clients' ids]}
ids = {}	# = {id:(username,port,ip_address)}

# udp socket
UDP_IP = socket.gethostbyname(socket.gethostname())
UDP_PORT = 12346
UDPs = socket.socket(socket.AF_INET,socket.SOCK_DGRAM) 
UDPs.bind((UDP_IP, UDP_PORT)) 


# tcp socket
s = socket.socket()         # Create a socket object
print socket.gethostname() # Get local machine name
port = 12345                # Reserve a port for your service.
s.bind(("paul", port))        # Bind to the port
s.listen(5)                 # Now wait for client connection.

read_list = [s]
timeout = 20
while True:
    readable, writable, errored = select.select(read_list, [], [],timeout)
    if not readable:
    	print "Timeout expired"
    	checkDeadClients(UDPs,ids,groups)
    	timeout = 20
    for sock in readable:
        if sock is s:
            c,addr = s.accept()
            read_list.append(c)
            print "Connection from", addr
        else:
            mes = sock.recv(1024)
            if mes:
				words = mes.split("antepia")
				username = words[0]
				print 'Receive username or id {}'.format(username)
				command = words[1]
				print 'Receive command {}'.format(command)
				words = command.split()	
				w1 = words[0]
				if w1[0:2] == "!j" and len(words) == 2:
					idC = int(username)
					# ean uparxei hdh to group tote uparxoun palia melh ta 
					# opoia 8a prepei na enhmerw8oun gia thn eisagwgh tou neou melous 
					if findGroup(words[1]):
						print "Bre8hkan palia melh!!"
						sendToOldMembers(groups[words[1]],idC,words[1],UDPs)
					insertGroup(idC,words[1])				# eisagwgh tou neou melous sth domh 'groups'
					# send list of member usernames, ids, ips and ports
					out = str(groups[words[1]])+ "##Server##Join" + sendInfoMembersOf(words[1])
					c.send(out)			#send list of memebers' ids
					

				elif w1[0:2] == "!e" and len(words) == 2:
					idC = int(username)
					removeFromGroup(idC,words[1])
					if words[1] in groups:				# mporei na exei diagrafei an den eixe melh apo thn removeFromGroup 
						# stelnei se ola ta palia melh (ean uparxoun) tou group oti o xrhsths vghke apo th sunomilia
						sendRemovingMember(groups[words[1]],idC,words[1],UDPs)

				elif w1[0:2] == "!q":
					idC = int(username)
					quit(idC)
					sendQuitingMember(idC,UDPs)

				elif w1[0:2] == "!w" and len(words) == 2:
					if words[1] in groups:
						c.send(sendMemberListOf(words[1]))
					else :
						print "Den yparxei auto to group!!!"
						c.send("False")

				elif w1[0:3] == "!lm" and len(words) == 2:
					outstr = printMemebersOf(words[1])
					c.send(outstr)

				elif w1[0:3] == "!lg":
					outstr = printGroups()
					c.send(outstr)

				elif w1[0:8] == "register" and len(words) == 2:
					i = str(register(username,words[1],addr[0]))
					c.send(i)

				else:
					print "Server received wrong command"

				sock.close()
				read_list.remove(sock)
				print 'Close the connection'
            else:
            	# It will never run!
            	print "Error"

