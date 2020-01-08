#! coding:utf-8

import threading
import time 

import multiprocessing 

from Robot import *

class RstException( Exception ):
    def __init__( self, *args ):
        super(RstException, self).__init__( *args )
        
class MyRobo( Robot ):
    def __init__(self, robot_type = "MRX-T4" ):
        super( MyRobo, self ).__init__( robot_type )
        self.mEnd = False 
        self.mCount = 0
        pass 

    # process the mission
    def proc( self, waitProc, page, dst,  paused = 0):
        # x,y,z,t

        self.mEnd = False 

        print ("dst", dst )
        
        if paused == 1:
            # 暂停模式
            self.goto(dst[0], dst[1], dst[2], 1, 23)
            self.waitStop( 23, waitProc )
        else:
            # 运行模式
            self.call(page)
            self.waitStop( page, waitProc )
        
        self.mEnd = True

    def isEnd( self ):
        return self.mEnd

         
class TransmissionTo( threading.Thread ):
    def __init__( self, name, *arg ):
        super(TransmissionTo,self).__init__(name = name)

        self.mContext = arg[0]
        self.mRobo = arg[1]
        self.mProc = arg[2]
        self.mPage = arg[3] 
        self.mArg = arg[4]      # dst pos (x,y,z,t) # dts pos (x1, y1, z1, x2, y2, z2, dt)
        
        self.mPaused = 0

        self.mCurrentPos = None

    def waitEnd( self ):
        # query the move status
        if ( self.mRobo.isEnd() ):
            return True 

        # paused
        if ( self.mContext.mPauseSema.acquire( timeout = 1) ):
            #print("pause received")                
            self.saveContext()                

            while( not self.mContext.mContinueSema.acquire( timeout = 1 ) ):
                #print("wait continue")                
                if ( self.mContext.mKillSema.acquire(timeout=1) ):
                    return True 
                else:                    
                    pass 

            self.continueContext() 

            return False
        # acquire fail
        else: 
            return False                     

    def saveContext( self ):
        # save the current
        # stop
        self.mRobo.forceStop()
        self.mPaused = 1
        pass 

    def continueContext( self ):
        # to again
        self.mProc( self.waitEnd, self.mPage, self.mArg , self.mPaused )
        pass 

    def run( self ):
        # run the item
        self.mProc( self.waitEnd, self.mPage, self.mArg )

        while( not self.waitEnd() ):
            pass                 

# abs pos
def robotMission( context, robo, page, proc, args ):
    """
    robot misssion
    """
    # get the abs pos 
    #roboCurPos = robo.get_current_position()
                      
    absPos = ( args[0], 
               args[1], 
               args[2],
               args[3])  # t

    print( absPos )               

    mission = TransmissionTo( "robo", context, robo, proc, page, absPos )

    mission.start()

    return mission
    

class SysContext( ):
    """
    context 
    """
    def __init__(self):
        self.mPauseSema = threading.Semaphore(0)
        self.mContinueSema = threading.Semaphore( 0 )
        self.mKillSema = threading.Semaphore(0)

    def pause(self):
        self.mPauseSema.release()

    def cont( self ):
        self.mContinueSema.release()

    def kill( self ):
        self.mKillSema.release()        

def waitMission( context, tRobo, proxy ):
    # config the io action
    toRunning = 0
    toPause = 1
    toRst = 1

    workingStat = "running"
    while( proxy.isAlive() ):
        
        x4State = tRobo.get_xin_1_state()
        
        xtState = tRobo.get_xin_2_state()

        if ( workingStat =='pause' ):
            if ( xtState == toRst ):
                
                #print("pause rst")
                
                context.kill()
                raise RstException('rst')

            elif ( x4State == toRunning ):
                context.cont() 
                workingStat = "running"
            else:
                pass                 

        elif ( workingStat == 'running' ):
            # to pause
            if ( xtState == toRst ):
                context.pause()
                context.kill()
                
                proxy.join()
                #print("running rst")
                raise RstException('rst')
            elif ( x4State == toPause ):
                context.pause()
                workingStat = "pause"
            else:
                pass                     
        else:
            pass 

        time.sleep( 0.01 )
    proxy = None 

def checkTerminate( robo ):
    def _checkTerminate( ):
        if robo.get_xin_2_state() == 1:
            
            # 停止手腕
            robo.wrist_stop()
            # 复位手腕
            #robo.wrist_reset()
            # 抛出异常，从新复位
            
            #print("send rst")
            
            raise RstException('rst')
            
        else:
            pass                             
    return _checkTerminate             

if __name__ == '__main__':
    
    context = SysContext()

    tRobo = MyRobo( "MRX-T4" )
    print( tRobo.get_current_position() )
