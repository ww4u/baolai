# -*- coding:utf-8 -*-

from interrupt import *

import platform

_platform = platform.system()

# if _platform != "Windows" :
#     from vxi11 import *
#     deviceIP = "127.0.0.1"
# else:
#     # deviceIP = "169.254.151.39"
#     deviceIP = "169.254.1.2"

#X1暂停 X2复位 X3动作 Y1接收到PLC信号后反馈信号（0为有效，1为无效） Y2完成动作后发出动作完成信号（0为有效，1为无效）

#1接收到PLC信号，Y1有效，给PLC反馈
def io_wait_reset(tRobo):
    """
    """
    if _platform != "Windows" :
        while tRobo.get_xin_2_state() == 0:
            time.sleep(0.2)
    else:
        print("wait for reset(r)")
        while input()!='r':
            pass

    tRobo.set_yout_1(1)
    time.sleep(0.5)    
        
    tRobo.set_yout_1(0)
    tRobo.set_yout_2(1)

def io_start(tRobo):
    if _platform != "Windows" :
        while tRobo.get_xin_3_state() == 0:
            time.sleep(0.2)
            if tRobo.get_xin_2_state() == 1:
                raise RstException('rst')
    else:
        print("wait for starting(g,r)")
        while True:
            k =input()
            if k == 'g':
                break 
            elif k == 'r':
                raise RstException('rst')
            else:
                pass 
        
    tRobo.set_yout_1(0)
    tRobo.set_yout_2(1)
        
#2运行结束后，Y2有效，给PLC运送完成信号
def io_end(tRobo):
    tRobo.set_yout_1(1)
    tRobo.set_yout_2(0)

#3机器人Y1 Y2信号复位，设置为无效
def io_reset(tRobo):
    tRobo.set_yout_1(1)
    tRobo.set_yout_2(1)


def mission_run( context, tRobo, page, proc ):
    """
    运行波表
    """
    def _mission( pt ):
        proxy = robotMission( context, tRobo, page, proc, pt )
        waitMission(context, tRobo, proxy)
    return _mission                

def doPreMission( context, robo, mission ):

    # check the current pos 
    #nowPos = robo.get_current_position()
    #dist = robo.eulaDistance(nowPos, mission["src"])
    #print("error", dist)
    #if (dist > 1):
        #robo.goto(mission["src"][0], mission["src"][1], mission["src"][2], 0.5, 23)
        #robo.waitAtop(23)
        #pass
    
    #robo.call(mission["page"])
    #robo.waitAtop(mission["page"], proc)
    
    mission_run( context, tRobo, mission["page"], tRobo.proc )( mission['dst'] )



def preDotMission(context, preMission, missName, robo ):
    for missDot in preMission:
        if ( missName == missDot['name'] ):
            doPreMission( context, robo, missDot )
            # print( missDot )
            return True
    return False         
 
def wristProc( tRobo, waitProc = None ):
    def _proc( angle = 180.5 ):
        wave_table = -1
        #tRobo.wrist( angle, 1, proc = waitProc )
        if (angle > 0):
            wave_table = 20
            #tRobo.wrist_run(20)
        elif (angle < -100):
            wave_table = 21
            #tRobo.wrist_run(21)
        elif angle < 0 and angle >= -100:
            wave_table = 22
            #tRobo.wrist_run(22)
        else:
            return
        tRobo.wrist_run(wave_table)
        tRobo.wait_wrist( wave_table, proc = waitProc )  
    return _proc  

                  
def doMission( context, preMission, missName, robo ):
    if ( preDotMission( context, preMission, missName, robo ) ):
        return True 
    elif ( missName == 'goHome' ):
        robo.go_home(23)
        robo.wait_home_stop(23)        
        return True
    elif ( missName == 'wristPositive' ):
        wristProc( tRobo, checkTerminate(tRobo) )( 180 )
        return True 
    elif ( missName == 'wristNegative' ):
        wristProc( tRobo, checkTerminate(tRobo) )( -180 )
        return True
    elif (missName == 'wristUser1'):
        wristProc( tRobo, checkTerminate(tRobo) )( 20 )
        return True
    elif (missName == 'wristUser2'):
        wristProc( tRobo, checkTerminate(tRobo) )( 0 )
        return True
    elif (missName == 'wristUser3'):
        wristProc( tRobo, checkTerminate(tRobo) )( 0 )
        return True    
    elif ( missName == 'io_start' ):
        # wait io
        io_start(tRobo)
        return True 
    elif ( missName == 'io_end' ):
        io_end(tRobo)
        return True
    else:
        #raise Exception('invalid proc')
        pass 



if __name__=="__main__":

    # 运行时间
    tScale = 1
    
    upDownScale = 0.5
    
    preDots = [
    
        #1 AtoB    
        {"name": "AtoB", 
        "page": 0,
        "src": (250,0,512,0),
        "dst": (15.5, 430, 475,0 ),
        "t": 1.5*tScale 
        },  
 
         #2 BtoC       
        {"name": "BtoC", 
        "page": 1,
        "src":(15.5, 430, 475,0 ),
        "dst": (15.5, 430, 426.8,0 ), 
        "t": 1*tScale 
        },

         #3 CtoB        
        {"name": "CtoB", 
        "page": 2,
        "src": (15.5, 430, 426.8,0 ),
        "dst": (15.5, 430, 475,0 ),
        "t": 0.5*tScale 
        },

         #4 BtoA
        {"name": "BtoA", 
        "page": 3,
        "src": (15.5, 430, 475,0 ),
        "dst": (250,0,512,0 ),
        "t": 1.5*tScale 
        },

        #5 AtoD1        
        {"name": "AtoD1", 
        "page": 4,
        "src": (250,0,512,0),
        "dst": (384.5, -20, 230,0 ),
        "t": 1*tScale 
        },

        #6 D1toE1        
        {"name": "D1toE1", 
        "page": 5,
        "src": (384.5, -20, 230,0 ),
        "dst": (384.5, -20, 200,0 ),
        "t": 0.6*tScale 
        },
    
        #7 E1toD1        
        {"name": "E1toD1", 
        "page": 6,
        "src": (384.5, -20, 200,0 ),
        "dst": (384.5, -20, 230,0 ),
        "t": 0.6*tScale 
        },

        #8 D1toA       
        {"name": "D1toA", 
        "page": 7,
        "src": (384.5, -20, 230,0 ),
        "dst": ( 250, 0, 512, 0 ),
        "t": 1*tScale 
        },

        #9 AtoD2        
        {"name": "AtoD2", 
        "page": 8,
        "src": (250,0,512,0),
        "dst": (323.5, -16.5, 230,0 ),
        "t": 1*tScale 
        },

        #10 D2toE2        
        {"name": "D2toE2", 
        "page": 9,
        "src": (323.5, -16.5, 230,0 ),
        "dst": (323.5, -16.5, 198.5,0 ),
        "t": 0.6*tScale 
        },

        #11 E2toD2        
        {"name": "E2toD2", 
        "page": 10,
        "src": (323.5, -16.5, 198.5,0 ),
        "dst": (323.5, -16.5, 230,0 ),
        "t": 0.6*tScale 
        },

        #12 D2toA        
        {"name": "D2toA", 
        "page": 11,
        "src": (323.5, -16.5, 230,0 ),
        "dst": (250, 0, 512,0 ),
        "t": 1*tScale 
        },

        #13 AtoD3       
        {"name": "AtoD3", 
        "page": 12,
        "src": (250,0,512,0),
        "dst": (261.5, -13, 230,0 ),
        "t": 1*tScale 
        },
 
         #14 D3toE3      
        {"name": "D3toE3", 
        "page": 13,
        "src": (261.5, -13, 230,0 ),
        "dst": (261.5, -13, 197,0 ),
        "t": 0.6*tScale 
        },    

         #15 E3toD3        
        {"name": "E3toD3", 
        "page": 14,
        "src": (261.5, -13, 197,0 ),
        "dst": (261.5, -13, 230,0 ),
        "t": 0.6*tScale 
        },    

         #16 D3toA        
        {"name": "D3toA", 
        "page": 15,
        "src": (261.5, -13, 230,0 ),
        "dst": (250,0,512,0),
        "t": 1*tScale 
        },      

        #17 AtoD4        
        {"name": "AtoD4", 
        "page": 16,
        "src": (250,0,512,0),
        "dst": (199.5,-9.5, 230,0 ),
        "t": 1*tScale 
        },
        
        #18 D4toE4
        {"name": "D4toE4", 
        "page": 17,
        "src": (199.5,-9.5, 230,0 ),
        "dst": (199.5,-9.5, 195.3,0 ),
        "t": 0.6*tScale 
        },

        #19 E4toD4       
        {"name": "E4toD4", 
        "page": 18,
        "src": (199.5,-9.5, 195.3,0 ),
        "dst": (199.5,-9.5, 230,0 ),
        "t": 0.6*tScale 
        },

        #20 D4toA        
        {"name": "D4toA", 
        "page": 19,
        "src": (199.5,-9.5, 230,0 ),
        "dst": (250, 0, 512,0 ),
        "t": 1*tScale 
        },   
    ]
    
    missions = list() 

    missions = [
                
    #针1     
        #原点到研磨机，抓针
        "io_start",
        "AtoB",
        "BtoC",
        "io_end",        

        #研磨机到安全位置,换爪子1 
        "io_start",
        "CtoB",
        "wristPositive",        
        "io_end",           
        
        #安全位置到研磨机，放针
        "io_start",
        "BtoC",
        "io_end",        

        #研磨机到安全位置，准备放到料盘
        "io_start",
        "CtoB",
        "BtoA",
        "io_end",           

    
        #安全位置到料盘，抓料
        "io_start",
        "AtoD1",
        "D1toE1",
        "io_end", 
        
        #料盘到针1上方，换爪子2
        "io_start",
        "E1toD1",
        "wristNegative",
        "io_end", 
                  
        #针1上方到料盘，抓料
        "io_start",
        "D1toE1",
        "io_end", 
                 
        #料盘到原点
        "io_start",
        "E1toD1",
        "D1toA",
        "io_end",      





    #针2     
        #原点到研磨机，抓针
        "io_start",
        "AtoB",
        "BtoC",
        "io_end",        

        #研磨机到安全位置,换爪子1 
        "io_start",
        "CtoB",
        "wristPositive",        
        "io_end",           
        
        #安全位置到研磨机，放针
        "io_start",
        "BtoC",
        "io_end",        

        #研磨机到安全位置，准备放到料盘
        "io_start",
        "CtoB",
        "BtoA",
        "io_end",           


        #安全位置到料盘，抓料
        "io_start",
        "AtoD2",
        "D2toE2",
        "io_end", 
        
        #料盘到针2上方，换爪子2
        "io_start",
        "E2toD2",
        "wristNegative",
        "io_end", 
                  
        #针2上方到料盘，抓料
        "io_start",
        "D2toE2",
        "io_end", 
                 
        #料盘到原点
        "io_start",
        "E2toD2",
        "D2toA",
        "io_end", 





    #针3     
        #原点到研磨机，抓针
        "io_start",
        "AtoB",
        "BtoC",
        "io_end",        

        #研磨机到安全位置,换爪子1 
        "io_start",
        "CtoB",
        "wristPositive",        
        "io_end",           
        
        #安全位置到研磨机，放针
        "io_start",
        "BtoC",
        "io_end",        

        #研磨机到安全位置，准备放到料盘
        "io_start",
        "CtoB",
        "BtoA",
        "io_end",           

    
        #安全位置到料盘，抓料
        "io_start",
        "AtoD3",
        "D3toE3",
        "io_end", 
        
        #料盘到针3上方，换爪子3
        "io_start",
        "E3toD3",
        "wristNegative",
        "io_end", 
                  
        #针3上方到料盘，抓料
        "io_start",
        "D3toE3",
        "io_end", 
                 
        #料盘到原点
        "io_start",
        "E3toD3",
        "D3toA",
        "io_end", 





    #针4     
        #原点到研磨机，抓针
        "io_start",
        "AtoB",
        "BtoC",
        "io_end",        

        #研磨机到安全位置,换爪子1 
        "io_start",
        "CtoB",
        "wristPositive",        
        "io_end",           
        
        #安全位置到研磨机，放针
        "io_start",
        "BtoC",
        "io_end",        

        #研磨机到安全位置，准备放到料盘
        "io_start",
        "CtoB",
        "BtoA",
        "io_end",           

    
        #安全位置到料盘，抓料
        "io_start",
        "AtoD4",
        "D4toE4",
        "io_end", 
        
        #料盘到针4上方，换爪子4
        "io_start",
        "E4toD4",
        "wristNegative",
        "io_end", 
                  
        #针4上方到料盘，抓料
        "io_start",
        "D4toE4",
        "io_end", 
                 
        #料盘到原点
        "io_start",
        "E4toD4",
        "D4toA",
        "goHome",
        "io_end",

        ]

    context = SysContext()

    tRobo = MyRobo( "MRX-T4" )
    io_reset(tRobo)
    print( tRobo.get_current_position() )
    

    # 下载 爪子波表
    tRobo.preWrist(180, 1, 20)
    tRobo.preWrist(-180, 1, 21)
    tRobo.preWrist(-100, 1, 22)
    
    # 下载波表
    for dot in preDots:
        print("page:", dot['page'])
        print("t:", dot['t'])
        tRobo.download(dot['src'][0], dot['src'][1], dot['src'][2],
                       dot['dst'][0], dot['dst'][1], dot['dst'][2],
                       dot['t'], 
                       dot['page'])
        tRobo.wait_download(dot['page'])      
    

    io_reset(tRobo)
    # 
    wristAngle = 180.7
    
    io_wait_reset(tRobo)

    currentPos = tRobo.get_current_position()
    if currentPos[2] <= 470: 
        
        tRobo.gotor(0, 0, (470 - currentPos[2]) + 5, 1, 23)
        tRobo.wait_run_stop(23)
    
    wristProc( tRobo, checkTerminate(tRobo) )( -100 ) 
    
    tRobo.go_home(23)
    tRobo.wait_home_stop(23)

    io_end(tRobo) 

    while True:

        try:
            """
            io_start(tRobo)
             # 此函数时运行上一个点，并下载当前点
            mission( context, tRobo, 0, tRobo.proc )( (400, 180, 312, 250, 0, 512, 10) )
            
            mission( context, tRobo, 1, tRobo.proc )( (250, 0, 512, 400, 180, 312, 10) )
            
            io_end(tRobo)
            """
            
            # TODO func
            
            #timeList = list()
            #errList = list() 
            #iterTimes = 1
            
            #for i in range( iterTimes ):
                #t1 = time.time() 
            for missName in missions:
                doMission( context, preDots, missName, tRobo )
                    #print(missName)
                #t2 = time.time()
                #timeList.append( t2-t1 )
                
            #print( iterTimes, max(timeList), min(timeList) )
        
             
        except RstException as e:
            # \todo to home
            
            #print("----------------------RST---------------------")
            tRobo.forceStop()
            time.sleep(0.5)
            #复位手腕
            
            
            tRobo.set_yout_1(1)
            time.sleep(0.5)
            
            #添加手腕运动，回零位可能出现反方向运动
            tRobo.set_yout_1(0)
            tRobo.set_yout_2(1)
            #  
            
            
            
            #tRobo.gotor(0, 0, 50, 2)
            #if tRobo.wait_run_Atop() == 0:
                #print("go run pass")
            #else:
                #print("go run faild")
                
            #tRobo.go_home(1)

            #if tRobo.wait_home_Atop() == 0:
                #pass
            
            currentPos = tRobo.get_current_position()
            if currentPos[2] <= 470: 
        
                tRobo.gotor(0, 0, (470 - currentPos[2]) + 5, 1, 23)
                tRobo.wait_run_stop(23)
                
            wristProc( tRobo, checkTerminate(tRobo) )( -100 )
            
            tRobo.go_home(23)
            tRobo.wait_home_stop(23)            
            
            #pos = tRobo.get_current_position()
            #print("CurrentPos:", pos)
            #print("================>> dx: %s, dy: %s, dz: %s" % (pos[0]-250.0, pos[1], pos[2]-512.0 ) )
            #tRobo.download(250, 0, 512, 150, 200, 512, 1, 0)
            #tRobo.download(250, 0, 512, 400, 180, 312, 1, 0)
            #tRobo.wait_download(0)  

            tRobo.set_yout_1(1)
            tRobo.set_yout_2(0)           
            
            pass 
        else:
            pass 
        finally:
            pass            

