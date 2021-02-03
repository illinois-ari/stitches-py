from stitches_py.resources import system_of_systems, sos_subsystem, sos_connection

from PingRequest import PingRequest
from PongResponse import PongResponse
from PingRequester import PingRequester
from PongResponder import PongResponder

@system_of_systems()
class PingPong:
    """
    A SoS for playing PingPong.
    """

    @sos_subsystem()
    def pinger(self) -> PingRequester:
        """ Subsystem sending ping requests """
        pass


    @sos_subsystem()
    def ponger(self) -> PongResponder:
        """ Subsystem replying with pong responses """
        pass


    @sos_connection('pinger', 'ping', 'ponger', 'pong')
    def ping_to_pong(self, msg: PingRequest) -> PingRequest:
        """Route PingRequests from the ping interface on the pinger to ponger. """
        pass


    @sos_connection('ponger', 'pong', 'pinger', 'ping_pong')
    def pong_to_pingpong(self, msg: PongResponse) -> PongResponse:
        """ Route PingRequests from pinger to ponger. """
        pass

    
