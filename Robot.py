# -*- coding:utf-8 -*-

import time
import threading
import math

import platform

_platform = platform.system()

if _platform != "Windows" :
    from vxi11 import *
    deviceIP = "127.0.0.1"
else:
    # deviceIP = "169.254.151.39"
    deviceIP = "169.254.1.2"

# print(_platform)

# print(platform.uname())
if _platform == "Windows": #and platform.uname()[2] == 10 :
    try:
        #import win_unicode_console
        #win_unicode_console.enable()
        # print("test")
        from visa import * 
        from pyvisa import *
    except ImportError as e:
        print( e.msg )  


#R = threading.Lock()


PAGE_TABLE = ["MAIN", "SMALL", "P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8",
              "P9", "P10", "P11", "P12", "P13", "P14", "P15", "P16", "P17", "P18", "P19", "P20", "P21", "P22"]

#"""

def visa_opra():
    m = ResourceManager()
    
#    print(m.list_resources())
    
    #inst = m.open_resource("USB0::0xA1B2::0x5722::MRHT00000518C40044::INSTR")
    
    #inst = m.open_resource("USB0::0xA1B2::0x5722::MRHT00000518C40056::INSTR")

    print("IP: ", deviceIP)
    inst = m.open_resource("TCPIP0::%s::inst0::INSTR" % deviceIP)

    inst.set_visa_attribute( constants.VI_ATTR_TMO_VALUE, 10000 )    

    return inst
#"""

class Robot(object):
    
    def __init__(self, robot_type = "MRX-T4"):
        """  """
        self._robot_type = robot_type
        self._robot = None
        self._device_name = ""
        
        
        
        self._lock = threading.RLock()
        
        # 创建连接

        if _platform == "Windows" :
            self._inst = visa_opra()
        else:
            self._vxi11 = Vxi11(deviceIP)

        
        
        # 搜索设备
        ret = self._search_device()
        if ret == 0:
            #构建机器人
            ret = self._create_robot()
            self._set_io_mode()
        else:
            pass
          
    
    def _write(self, msg):
        """
        发送信息
        """
        self._lock.acquire()
        if _platform == "Windows" :
            self._inst.write(msg)
        else:
            msg += '\n'
            self._vxi11.send(msg)

        self._lock.release()
        
    def _read(self):
        """
        读取数据
        """
        self._lock.acquire()
        
        if _platform == "Windows" :
            ret = self._inst.read()
        else:
            ret = self._vxi11.receive()

        self._lock.release()
        if ret == None:
            return None
        else:
            return ret
        
        
    def _query(self, msg):
        """
        
        """
        self._lock.acquire()
        if _platform == "Windows" :
            self._inst.write(msg)
        else:
            msg += '\n'
            self._vxi11.send(msg)
        
        if _platform == "Windows" :
            ret = self._inst.read()
        else:
            ret = self._vxi11.receive()
        self._lock.release()
        
        if ret == None:
            return None
            
        
        if ret.find('\n') >= 0:
            ret = ret.replace('\n', '')
        
        return ret
        
    def _search_device(self):
        """
        搜索设备，且设备类型为：MRQM2305
        有：返回设备号；
        没有：返回-1
        """

        _device_type = ""
        
        # test
        ret = self._query("*IDN?")
        
        print("*IDN? : %s" % ret)
        
        # search device
        self._write(":DEVICE:SEAR")
        # 搜索设备延时
        time.sleep(2)
        
        # 获取设备名
        self._device_name = self._query(":DEVICE:NAME?")
        print("device name: %s" % self._device_name)
        
        # 获取设备类型
        
        _device_type = self._query(":DEVICE:TYPE? %s" % (self._device_name))
        print("device type: %s" % _device_type)        
        
        #if _device_type.find("MRQM2305") >= 0:
        if _device_type == "MRQM2305":
            return 0
        else:
            return -1
        
        
    def _create_robot(self):
        """
        创建机器人，使用设备,必须存在设备时进行构建
        return： -1 -> faild
                 0  -> pass
        """
        
        # :ROBOT:ALLOC? MRX-T4, ( 0@ 513, 0@ 513, 0@ 513, 0@ 513, 0@ 513)
        self._robot = ""
        self._robot = self._query(":ROBOT:ALLOC? %s,(0@%s,1@%s,2@%s,3@%s)"
                                  % (self._robot_type, 
                                     self._device_name,
                                     self._device_name,
                                     self._device_name,
                                     self._device_name))
        print(self._robot)
        
        
        if self._robot == "":
            return -1
        else:
            return 0
    
    def _set_io_mode(self):
        """
        IO 需要设置为工程模式，读取IO的值
        """
        self._write(":PROJ:STAT ON")
        
    def _page_transform(self, page):
        """
        波表转化
        """
        if page >= 0 and page < 24:
            return PAGE_TABLE[page]
        else:
            return None
        

    
    def set_step(self, step = 0):
        """
        设置插值步长        
        """
        self._write(":ROBOT:INTERPOLATe:STEP %s,%d" % (self._robot, step))
        
        
    def get_step(self, step = 0):
        """
        查新插值步长
        """
        ret = self._query(":ROBOT:INTERPOLATe:STEP? %s" % (self._robot))
        
    def go_home(self, page = 0):
        """
        回零
        """
        _page = self._page_transform(page)
        
        # 设置 home page
        
        self._write(":ROBOT:HOME:WAVETABLE %s,%s" % (self._robot, _page))
        time.sleep(0.2)
        self._write(":ROBOT:HOME:RUN %s" % self._robot)
        time.sleep(0.2)
    
    def wait_home_stop(self, page = 0, tmo = 20):
        """
        等待回零位，完成
        return: 0 -> pass
                -1 -> faild tmo
        """
        
        _page = self._page_transform(page)
        
        ret = ""
        while ret != "IDLE": # and tmo != 0:
            tmo -= 1
            time.sleep(1)
            ret = self._query(":ROBOT:HOME:STAT? %s" % (self._robot))
            #print("wait_home_stop:",ret)
            
        
        if tmo > 0:
            return 0
        else:
            return -1   
    
    def preWrist(self, angle, t = 2, page = 9, proc = None):
        """
        下载
        """
        _page = self._page_transform(page)
        time.sleep(0.1)
        self._write("DEV:MRQ:PVT:CONF %s,3,%s,CLEAR" % (self._device_name, _page))
        time.sleep(0.1)
        self._write("DEV:MRQ:PVT:VAL %s,3,%s,0,0,0" % (self._device_name, _page))
        time.sleep(0.1)
        self._write("DEV:MRQ:PVT:VAL %s,3,%s,%d,0,%d" % (self._device_name, _page, angle, t))
        time.sleep(0.1)
        self._write("DEV:MRQ:PVT:CONF %s,3,%s,END" % (self._device_name, _page))
        time.sleep(0.1) 
        
        ret = ""
        # while ret != "READY" :
        while ret != "READY" and ret != "CALCEND":
            #tmo -= 1
            time.sleep(1)
            ret = self._query("DEV:MRQ:PVT:STATE? %s,3,%s" % (self._device_name, _page))
            #print("preWrist:",ret)
            if ( proc != None ):
                proc()    
            else:
                time.sleep(1)
        
    
    def wrist(self, angle, t = 2, page = 9, proc = None ):
        """
        使用PVT方式，运动 wrist
        """
        
        _page = self._page_transform(page)
        time.sleep(0.1)
        self._write("DEV:MRQ:PVT:CONF %s,3,%s,CLEAR" % (self._device_name, _page))
        time.sleep(0.1)
        self._write("DEV:MRQ:PVT:VAL %s,3,%s,0,0,0" % (self._device_name, _page))
        time.sleep(0.1)
        self._write("DEV:MRQ:PVT:VAL %s,3,%s,%d,0,%d" % (self._device_name, _page, angle, t))
        time.sleep(0.1)
        self._write("DEV:MRQ:PVT:CONF %s,3,%s,END" % (self._device_name, _page))
        time.sleep(0.1)
        
        # 等待pvt解算完成
        ret = ""
        tmo = 20
        while ret != "READY" and tmo != 0:
            tmo -= 1
            time.sleep(1)
            ret = self._query("DEV:MRQ:PVT:STATE? %s,3,%s" % (self._device_name, _page))
            #print("wrist:",ret)
            if ( proc != None ):
                proc()
            
        #time.sleep(0.5)
        
        # 运行 pvt
        if tmo > 0:
            self._write("DEV:MRQ:MOT:RUN %s,3,%s" % (self._device_name, _page))
            return 0
        else:
            return -1        
    
    def wrist_run( self, page = 0):
        """
        """
        _page = self._page_transform(page)
        self._write("DEV:MRQ:MOT:RUN %s,3,%s" % (self._device_name, _page))
    
    def wait_wrist(self, page = 9, proc = None ):
        """
        等到 wrist 运行结束
        """
        _page = self._page_transform(page)
        
        count = 20
        
        tmo = 20
        ret = ""
        while ret != "READY" and tmo:
            
            count -= 1
            tmo -= 1
            time.sleep(0.5)
            ret = self._query("DEV:MRQ:MOT:RUN:STAT? %s,3,%s" % (self._device_name, _page))
            #print("wait_wrist:",ret)
            
            if (count == 0):
                count = 10
                if ( proc != None ):
                    proc()
                    #pass
        
        #self._write("DEV:MRQ:MOT:RESET %s,3,%s" % (self._device_name, _page))
        #time.sleep(0.1) 
              
        #if tmo > 0:
            #return 0
        #else:
            #return -1
        
        
    def wrist_reset(self, page = 9):
        """
        复位手腕
        """
        _page = self._page_transform(page)
        self._write("DEV:MRQ:MOT:RESET %s,3,%s" % (self._device_name, _page))
        time.sleep(0.1) 
    
    def wrist_stop(self, page = 9):
        """
        停止腕关节
        """
        _page = self._page_transform(page)
        self._write("DEV:MRQ:MOT:STOP %s,3,%s" % (self._device_name, _page))
        self.wrist_reset(page)
        
    
    def goto(self, x, y, z, t, page = 0):
        """ 不插值 """
        
        # 转化波表
        _page = self._page_transform(page)
        
        self._write(":ROBOT:WAVETABLE %s,%s" % (self._robot, _page))
        time.sleep(0.2)        
        
        # 运行
        self._write(":ROBOT:MOV %s,%d,%d,%d,%d,%s"
                    % (self._robot,
                       x,
                       y,
                       z,
                       t,
                       _page))
        
        time.sleep(0.5)
    
    def gotor(self, x, y, z, t, page = 0):
        """ 相对位置移动，不插值 """
        # 转化波表
        _page = self._page_transform(page)
        
        self._write(":ROBOT:WAVETABLE %s,%s" % (self._robot, _page))
        time.sleep(0.2)        
        
        # 运行
        self._write(":ROBOT:MOV:RELAT %s,%d,%d,%d,%d,%s"
                    % (self._robot,
                       x,
                       y,
                       z,
                       t,
                       _page))
        
        time.sleep(0.5)
        
    
    def gotol(self, x, y, z, t, page = 0):
        """ 线性插值 """
        
        # 转化波表
        _page = self._page_transform(page)
        
        self._write(":ROBOT:WAVETABLE %s,%s" % (self._robot, _page))
        time.sleep(0.2)        
        
        self._write(":ROBOT:MOV:LIN %s,%d,%d,%d,%d,%s"
                    % (self._robot,
                       x,
                       y,
                       z,
                       t,
                       _page))
        
        time.sleep(0.5)
    
    def gotolr(self, x, y, z, t, page = 0):
        """
        线性插值，相对运动
        """
        # 转化波表
        _page = self._page_transform(page)
        
        self._write(":ROBOT:WAVETABLE %s,%s" % (self._robot, _page))
        time.sleep(0.2)        
        
        self._write(":ROBOT:MOV:LIN:RELAT %s,%d,%d,%d,%d,%s"
                    % (self._robot,
                       x,
                       y,
                       z,
                       t,
                       _page))
        
        time.sleep(0.5)
        
        
    def wait_run_stop(self, page = 0, tmo = 20):
        """
        等待运行结束
        """
        
        _page = self._page_transform(page)
        
        ret = ""
        while ret != "IDLE" and ret != "STOP": # and tmo != 0:
            #tmo -= 1
            time.sleep(1)
            ret = self._query(":ROBOT:STAT? %s,%s" % (self._robot, _page))
            print("wait_run_stop:",ret)
        
        if tmo > 0:
            return 0
        else:
            return -1        
        
    # wait stop indifinitely
    def waitStop(self, page = 0, detectproc=None ):
        """
        等待运行结束
        """
        
        count = 20
        
        _page = self._page_transform(page)
        
        ret = ""
        while ret != "IDLE" and ret != "STOP":
            ret = self._query(":ROBOT:STAT? %s,%s" % (self._robot, _page))
            #print("waitStop:",ret)
            time.sleep(0.5)
            count -= 1
            
            if (count == 0):   
                count = 10
                if ( detectproc != None ):
                    detectproc()
                    pass
                else:
                    pass
                #time.sleep( 1 )     
    
    def preMove(self, page, pt1, pt2, dt, mode = 0, step = 0):
        """
        
        """
        _page = self._page_transform(page)
        
        # clear point
        self._write("ROBOT:POIN:CLEAR %s" % (self._robot))
        #time.sleep(0.2)
        
        # download point
        self._write("ROBOT:POIN:LOAD %s,%s,%s,%s,%s,%s,%s,%s"
                    % (self._robot,
                       pt1[0],  
                       pt1[1],
                       pt1[2],
                       0,
                       0,
                       mode,
                       step))
        #time.sleep(0.1)
        
        # download point
        self._write("ROBOT:POIN:LOAD %s,%s,%s,%s,%s,%s,%s,%s"
                    % (self._robot,
                       pt2[0],  
                       pt2[1],
                       pt2[2],
                       0,
                       dt,
                       mode,
                       step))
        #time.sleep(0.1)
        
        # resolve point
        self._write("ROBOT:POIN:RESOLVe %s,%s" % (self._robot, _page))        
        
    
    def download(self, x1, y1, z1, x2, y2, z2, dt, page = 0, mode = 0, step = 0):
        """
        x1, y1, z1, t1 : start pos
        x2, y2, z2, t2 : end pos
        
        page: 
        
        mode: 0 -> 不插值
              1 -> 线性插值
        step: 插值步长
        
        """
        _page = self._page_transform(page)
        
        # clear point
        self._write("ROBOT:POIN:CLEAR %s" % (self._robot))
        #time.sleep(0.2)
        
        # download point
        self._write("ROBOT:POIN:LOAD %s,%s,%s,%s,%s,%s,%s,%s"
                    % (self._robot,
                       x1,  
                       y1,
                       z1,
                       0,
                       0,
                       mode,
                       step))
        #time.sleep(0.1)
        
        # download point
        self._write("ROBOT:POIN:LOAD %s,%s,%s,%s,%s,%s,%s,%s"
                    % (self._robot,
                       x2,  
                       y2,
                       z2,
                       0,
                       dt,
                       mode,
                       step))
        #time.sleep(0.1)
        
        # resolve point
        self._write("ROBOT:POIN:RESOLVe %s,%s" % (self._robot, _page))
        
        
    def wait_download(self, page = 0, detectproc = None):
        """
        等待下载点
        return： 0 -> pass
                 -1 -> faild
        """
        _page = self._page_transform(page)
        
        #print("wait download page: %s" % (_page))
        
        ret = ""
        while ret != "READY": # and tmo != 0:
            time.sleep(1)
            ret = self._query(":ROBOT:STAT? %s,%s" % (self._robot, _page))     
            #print("wait_download:",ret)
            if ( detectproc != None ):
                detectproc()
            else:
                time.sleep( 1 )             
        
        
    def call(self, page = 0):
        """
        运行page
        """
        
        _page = self._page_transform(page)
        
        self._write("ROBOT:RUN %s,%s" % (self._robot, _page))
    
    def get_current_position(self):
        """
        """
        ret = self._query("ROBOT:CURRENT:POSITION? %s" % (self._robot))
        
        pos = str(ret).split(",")

        return ( float(pos[0]), float(pos[1]), float(pos[2]) )
    
    def get_current_angle(self):
        """
        """
        ret = self._query("ROBOT:CURRENT:ANGLE? %s" % (self._robot))
        angle = str(ret).split(",")
        
        return ( float(angle[0]), float(angle[1]), float(angle[2]), float(angle[3]) ) 
    
    def eulaDistance( self, a, b ):
        """
        eula ( a, b )
        """
        distance = math.sqrt( math.pow( (a[0]-b[0]),2 ) 
                                  + math.pow( (a[1]-b[1]),2 )
                                 + math.pow( (a[2]-b[2]),2 ) )
        return distance     
        
    def get_xin_1_state(self):
        """
        获取 IO
        """
        time.sleep(0.1)
        ret = self._query("PROJ:XREAD? X1")
        #print("x1: %s" % ret)
        if ret == "L":
            return 0
        elif ret == "H":
            #print("x1: %s" % ret)
            return 1
    
    def get_xin_2_state(self):
        """
        获取 IO
        """
        time.sleep(0.1)
        ret = self._query("PROJ:XREAD? X2")
        #print("x2: %s" % ret)
        if ret == "L":
            return 0
        elif ret == "H":
            #print("x2: %s" % ret)
            return 1        
        
    def get_xin_3_state(self):
        """
        获取 IO
        """
        time.sleep(0.1)
        ret = self._query("PROJ:XREAD? X3")
        #print("x3: %s" % ret)
        if ret == "L":
            return 0
        elif ret == "H":
            #print("x3: %s" % ret)
            return 1        
    
    def get_xin_4_state(self):
        """
        获取 IO
        """
        time.sleep(0.1)
        ret = self._query("PROJ:XREAD? X4")
        #print("x4: %s" % ret)
        if ret == "L":
            return 0
        elif ret == "H":
            #print("x4: %s" % ret)
            return 1        
        
    
    def set_yout_1(self, state):
        """
        设置 IO
        """

        if state == 0:
            self._write("PROJ:YWRITE Y1,L")
        elif state == 1:
            self._write("PROJ:YWRITE Y1,H")
        
    def set_yout_2(self, state):
        """
        设置 IO
        """

        if state == 0:
            self._write("PROJ:YWRITE Y2,L")
        elif state == 1:
            self._write("PROJ:YWRITE Y2,H")        
        
    def refresh_state(self, page = 0):
        """
        """
        _page = self._page_transform(page)
        
        ret = self._query(":ROBOT:STAT? %s,%s" % (self._robot, _page))
        print("refresh_state:",ret)
    
    def forceStop( self, page = 0 ):
        _page = self._page_transform(page)
        self._write("ROBOT:STOP %s,%s" % (self._robot, _page ))    

def wait_xin(robot):
    """
    """
    while True:
        #R.acquire()
        print("xin 1: %d" % robot.get_xin_1_state())
        print("xin 2: %d" % robot.get_xin_2_state())
        print("xin 3: %d" % robot.get_xin_3_state())
        time.sleep(1)
        #R.release()

def robot_run(robot, time):
    
        
    while True:
        
        robot.goto(230, 20, 412, 30)
        if robot.wait_run_stop(tmo = 40) == 0:
            print( robot.get_current_position() )
            print("go run pass")
            robot.wrist(180)
            robot.wait_wrist()
            print( robot.get_current_position() )
        else:
            print("go run faild")
        
        robot.goto(250, 0, 512, 30)
        if robot.wait_run_stop(tmo = 40) == 0:
            print( robot.get_current_position() )
            print("go run pass")
            robot.wrist(180)
            robot.wait_wrist()
            print( robot.get_current_position() )       
        else:
            print("go run faild")        
        

if __name__ == '__main__':
    """ test this class"""
    
    test = 0
    
    # 构建机器人
    robot = Robot("MRX-T4")
    
    # wait_xin(robot)
    
    # robot.go_home(23)
    # robot.wait_home_stop(23)     
    
    #robot.preWrist(-180, 1, 20)
    #robot.wrist_run(20)
    #robot.wait_wrist(20)
    
    
    #"""
    # 运行时间
    tScale = 1
    
    preDots = [
    
        #1 AtoB    
        {"name": "AtoB", 
        "page": 0,
        "src": (250,0,512,0),
        "dst": (14, 431, 465.5,0 ),
        "t": 1.5 
        },  
 
         #2 BtoC       
        {"name": "BtoC", 
        "page": 1,
        "src":(14, 431, 465.5,0 ),
        #"dst": (14, 431, 425.5,0 ),  
        "dst": (14, 431, 455.5,0 ), 
        "t": 1*tScale 
        },

         #3 CtoB        
        {"name": "CtoB", 
        "page": 2,
        "src": (14, 431, 455.5,0 ),
        "dst": (14, 431, 475.5,0 ),
        "t": 1*tScale 
        },

         #4 BtoA 
        {"name": "BtoA", 
        "page": 3,
        "src": (14, 431, 475.5,0 ),
        "dst": (250, 0, 512,0 ),
        "t": 1.5 
        },

        #5 AtoD1        
        {"name": "AtoD1", 
        "page": 4,
        "src": (250,0,512,0),
        "dst": (388, 0, 270,0 ),
        "t": 1*tScale 
        },

        #6 D1toE1        
        {"name": "D1toE1", 
        "page": 5,
        "src": (388, 0, 270,0 ),
        "dst": (388, 0, 207,0 ),
        "t": 1*tScale 
        },
    
        #7 E1toD1        
        {"name": "E1toD1", 
        "page": 6,
        "src": (388, 0, 207,0 ),
        "dst": (388, 0, 270,0 ),
        "t": 1*tScale 
        },

        #8 D1toA       
        {"name": "D1toA", 
        "page": 7,
        "src": (388, 0, 270,0 ),
        "dst": ( 250, 0, 512, 0 ),
        "t": 1*tScale 
        },

        #9 AtoD2        
        {"name": "AtoD2", 
        "page": 8,
        "src": (250,0,512,0),
        "dst": (326, 3, 270,0 ),
        "t": 1*tScale 
        },

        #10 D2toE2        
        {"name": "D2toE2", 
        "page": 9,
        "src": (326, 3, 270,0 ),
        "dst": (326, 3, 205,0 ),
        "t": 1*tScale 
        },

        #11 E2toD2        
        {"name": "E2toD2", 
        "page": 10,
        "src": (326, 3, 205,0 ),
        "dst": (326, 3, 270,0 ),
        "t": 1*tScale 
        },

        #12 D2toA        
        {"name": "D2toA", 
        "page": 11,
        "src": (326, 3, 270,0 ),
        "dst": (250, 0, 512,0 ),
        "t": 1*tScale 
        },

        #13 AtoD3       
        {"name": "AtoD3", 
        "page": 12,
        "src": (250,0,512,0),
        "dst": (264, 6.5, 270,0 ),
        "t": 1*tScale 
        },
 
         #14 D3toE3      
        {"name": "D3toE3", 
        "page": 13,
        "src": (264, 6.5, 270,0 ),
        "dst": (264, 6.5, 204,0 ),
        "t": 1*tScale 
        },    

         #15 E3toD3        
        {"name": "E3toD3", 
        "page": 14,
        "src": (264, 6.5, 204,0 ),
        "dst": (264, 6.5, 270,0 ),
        "t": 1*tScale 
        },    

         #16 D3toA        
        {"name": "D3toA", 
        "page": 15,
        "src": (264, 6.5, 270,0 ),
        "dst": (250,0,512,0),
        "t": 1*tScale 
        },      

        #17 AtoD4        
        {"name": "AtoD4", 
        "page": 16,
        "src": (250,0,512,0),
        "dst": (202, 10.5, 270,0 ),
        "t": 1*tScale 
        },
        
        #18 D4toE4
        {"name": "D4toE4", 
        "page": 17,
        "src": (202, 10.5, 270,0 ),
        "dst": (202, 10.5, 202,0 ),
        "t": 1*tScale 
        },

        #19 E4toD4       
        {"name": "E4toD4", 
        "page": 18,
        "src": (202, 10.5, 202,0 ),
        "dst": (202, 10.5, 270,0 ),
        "t": 1*tScale 
        },

        #20 D4toA        
        {"name": "D4toA", 
        "page": 19,
        "src": (202, 10.5, 270,0 ),
        "dst": (250, 0, 512,0 ),
        "t": 1*tScale 
        },   
    ]
    
    # 波表 0 回零
    robot.go_home(1)
    robot.wait_home_stop(1)    
    
    #dot = preDots[0]
    
    #robot.download(x1, y1, z1, x2, y2, z2, dt, page=0, mode=0, step=0)
    
    print(len(preDots))
    
    for dot in preDots:
        print(dot['page'])
    
    # 下载 波表
    for dot in preDots:
        print("page:", dot['page'])
        robot.download(dot['src'][0], dot['src'][1], dot['src'][2],
                       dot['dst'][0], dot['dst'][1], dot['dst'][2],
                       dot['t'], 
                       dot['page'])
        robot.wait_download(dot['page'])        
    
    
    while True:
    
        timeStart = time.time()
        for dot in preDots:
            # 运行波表
            robot.call(dot['page'])
            robot.waitStop(dot['page'])  

        print("time:", time.time() - timeStart)
    #"""
    
    
    
            
    
    
