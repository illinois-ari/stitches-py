import asyncio
import time
from uuid import uuid4

from stitches_py.resources import field, subfield, subsystem, ss_interface, ss_thread

from PingRequest import PingRequest
from PongResponse import PongResponse

@subsystem()
class PingRequester:
    """
    PingRequester
    """

    @ss_thread
    def _send_pings(self):
        """
        Thread to send pings at a predefined interval.
        """
        while not self._shutdown_requested: # Flag to detect shutdowns and exit gracefully.
           time.sleep(5)
           self._logger.warn('Sending ping')
           self.ping() # Trigger Out Interface by calling the bound method.
    
    @ss_interface
    def ping(self) -> PingRequest: # Return annotations designate Out Interfaces
        """
        Out interface which sends ping requests.
        """
        req = PingRequest()
        req.req_id = str(uuid4())
        req.send_ts = int(time.time()) # Convert ts to int

        return req

    @ss_interface
    def ping_pong(self, resp: PongResponse): # Input annotations designate In Interfaces.
        """
        In interface which receives pong responses generated from ping requests.
        """
        self._logger.warn(f'Received pong for ping ({resp.req_id}).')
