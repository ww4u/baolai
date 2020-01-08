#!/usr/bin/python3
# -*- coding:utf-8 -*-

from socket import *
import platform
import os
import struct

BUF_LEN = 1024
TIME_OUT = 10
NETLINK_HEAD_LEN = 16
GOAL_PROGRESS = "GreatShot"

def isWindows():
    return 'Windows' in platform.system()

def isLinux():
    return 'Linux' in platform.system()

def isArm():
    return 'arm' in platform.machine()

def find_pid_by_name():
    """  """
    if isLinux() == True:# and isArm() == True:
        cmd = "ps -eo pid,comm | grep -w %s | awk '{print $1}'"%(GOAL_PROGRESS)    
        result = os.popen(cmd, 'r')    
        return int(result.read())
    else:
        print("Platform not supported!")
        return None


class NetlinkSocket(object):
    """  """
    
    def __init__(self):
        """  """
        
        self._socket_fd = None
        self._self_pid = None
        self._goal_pid = find_pid_by_name()
        
        if isLinux() == True:# and isArm() == True:
            pass
        else:
            print("Platform not supported!")
        
        
    def creat_netlink_socket(self):
        self._socket_fd = socket(AF_NETLINK, SOCK_DGRAM, NETLINK_USERSOCK)
        self._self_pid = os.getpid()
        self._socket_fd.bind((self._self_pid, 0))
        self._socket_fd.setsockopt(SOL_SOCKET, SO_SNDBUF, BUF_LEN)
        self._socket_fd.setsockopt(SOL_SOCKET, SO_RCVBUF, BUF_LEN)
        self._socket_fd.settimeout(TIME_OUT)
        return self._socket_fd
    
            
    def send_msg(self, msg):
        """  """
        _msg = str(msg).encode('utf-8')
        _send_len = NETLINK_HEAD_LEN + len(msg)        
        _send_data = struct.pack('IHHII%ds'%(len(_msg)), _send_len, 0,0,0,self._self_pid, _msg)
        self._socket_fd.sendto(_send_data, (self._goal_pid, 0))
        
        
    def recv_msg(self):
        """  """
        _msg = None
        try:
            _msg = self._socket_fd.recvfrom(BUF_LEN)
        except Exception as e:
            print(e)
            return None        
        _data = struct.unpack('IHHII%ds'%(len(_msg[0]) - NETLINK_HEAD_LEN), _msg[0])
        return str(_data[5], encoding='utf-8')


if __name__ == '__main__':    
    """ test """
    
    ns = NetlinkSocket()
    ns.creat_netlink_socket() 
    #print(pid)
    
    count = 0
    
    while 1:
        ns.send_msg("*IDN?\n")
        recv = ns.recv_msg()
        print("count: %d, recv: %s"%(count, recv))
        count += 1