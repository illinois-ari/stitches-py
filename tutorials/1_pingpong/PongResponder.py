import asyncio
import time
from uuid import uuid4

from stitches_py.resources import field, subfield, subsystem, ss_interface, ss_thread

from PingRequest import PingRequest
from PongResponse import PongResponse

@subsystem()
class PongResponder:
    """
    PongResponder
    """

    @ss_interface
    def pong(self, req: PingRequest) -> PongResponse: # Interfaces can be both In and Out.
        """
        In/Out interface which receives ping requests and sends pong responses.
        """
        self._logger.info(f'Received ping ({req.req_id}).')
        resp = PongResponse()
        resp.req_id = req.req_id # Attach the request id for tracking.
        resp.recv_ts = int(time.time()) # Convert ts to int
        self._logger.warn(f'Replying with pong ({req.req_id}).')
        return resp