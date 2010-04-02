import time

from callback import Callback

class LongOpStatus(Callback):
    """LongOpStatus provides a way of communicating the status of a long
    running operations. The intended use is that when a long running operation
    is about to start it should create an instance of this class and emit
    it so that any listeners can pick it up and use it to record the status 
    of the operation.


    Signals
    =======
    
      op-heartbeat - emitted every 'interval' calls to heartbeat. 
      op-end       - emitted once when the operation completes.

    
    Example usage:

    class MyClass(Callback):

        __signals__ = {
	   'op-start'   : object
	}
    
        def long(self):
        status = LongOpStatus("doing long job", 100, 10)

            for i in xrange(0,99):
            time.sleep(0.1)
            status.heartbeat()

            status.end()
    

    class MyListener(object):

         def __init__(self):
         self._op = MyClass()
         self._op.connect('op-start', self.start)
         self._current_op = None

         def start(self,long_op):
         self._current_op.connect('op-heartbeat', self.heartbeat)
         self._current_op.connect('op-end', self.stop)

         def hearbeat(self):
         # update status display

         def stop(self):
         # close the status display
             self._current_op = None
    """

    __signals__ = {
	'op-heartbeat'   : None,
	'op-end'         : None
	}

    def __init__(self, msg="", 
                 total_steps=None, 
                 interval=1,
                 can_cancel=False):
        """
        @param msg: A Message to indicated the purpose of the operation.
        @type msg: string
        
        @param total_steps: The total number of steps that the operation 
        will perform.
        @type total_steps:
        
        @param interval: The number of iterations between emissions.
        @type interval:
        
        @param can_cancel: Set to True if the operation can be cancelled.
        If this is set the operation that creates the status object should
        check the 'should_cancel' method regularly so that it can cancel 
        the operation.
        @type can_cancel:
        """
        Callback.__init__(self)
        self._msg = msg
        self._total_steps = total_steps
        # don't allow intervals less that 1
        self._interval = max(interval,1) 
        self._can_cancel = can_cancel
        
        self._cancel = False
        self._count = 0
        self._countdown = interval
        self._secs_left = 0
        self._start = time.time()
        self._running = True

    def __del__(self):
        if self._running:
            self.emit('op-end')
            
    def heartbeat(self):
        """This should be called for each step in the operation. It will
        emit a 'op-heartbeat' every 'interval' steps. It recalcuates the
        'estimated_secs_to_complete' from the time taken for previous 
        steps.
        """
        self._countdown -= 1
        if self._countdown <= 0:
            elapsed = time.time() - self._start
            self._secs_left = \
        	( elapsed / self._interval ) \
        	* (self._total_steps - self._count)
            self._count += self._interval
            self._countdown = self._interval
            self._start = time.time()
            self.emit('op-heartbeat')

    def estimated_secs_to_complete(self):
        """Return the number of seconds estimated left before operation 
        completes. This will change as 'hearbeat' is called.
    
        @return: estimated seconds to complete.
        @rtype: int
        """
        return self._secs_left

    def cancel(self):
        """Inform the operation that it should complete.
        """
        self._cancel = True
        self.end()

    def end(self):
        """End the operation. Causes the 'op-end' signal to be emitted.    
        """
        self.emit('op-end')
        self._running = False

    def should_cancel(self):
        """Return true of the user has asked for the operation to be cancelled.
    
        @return: True of the operation should be cancelled.
        @rtype: bool
        """
        return self._cancel

    def can_cancel(self):
        """@return: True if the operation can be cancelled.
           @rtype: bool
           """
        return self._can_cancel

    def get_msg(self):
        """@return: The current status description messages.
           @rtype: string
           """
        return self._msg

    def set_msg(self, msg):        
        """Set the current description message.
        
        @param msg: The description message.
        @type msg: string
        """
        self._msg = msg
        
    def get_total_steps(self):
        """Get to total number of steps. NOTE: this is not the 
        number of times that the 'op-heartbeat' message will be
        emited. 'op-heartbeat' is emited get_total_steps/interval
        times.
        
        @return: total number of steps.
        @rtype: int
        """
        return self._total_steps

    def get_interval(self):
        """Get the interval between 'op-hearbeat' signals.
        
        @return: the interval between 'op-hearbeat' signals.
        @rtype: int
        """
        return self._interval 


if __name__ == '__main__':

    s = LongOpStatus("msg", 100, 10)

    def heartbeat():
        print "heartbeat ", s.estimated_secs_to_complete()

    def end():
        print "end"

    s.connect('op-heartbeat', heartbeat)
    s.connect('op-end', end)

    for i in xrange(0, 99):
        time.sleep(0.1)
        s.heartbeat()

    s.end()
    
