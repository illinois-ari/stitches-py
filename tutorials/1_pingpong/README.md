# PingPong
In this tutorial we will create some simple Subsystems and System of Systems (SoS) to demonstrate `stitches-py`

In this SoS a `PingRequester` will send a `PingRequest` to a `PongResponder` which will send a `PongResponse` back to the `PingRequester` upon receipt.


#### Fields
We first need to define what a `PingRequest` and `PongResponse` look like. We can use the `stitches-py` cli to generate scaffold code files.

```bash
./stitches-py ftg create-field PingRequest --empty
./stitches-py ftg create-field PongResponse --empty

# To see cli help
./stitches-py ftg create-field --help

# List new fields
./stitches-py ftg list-fields
```

There should now be two files in the `inputs/` directory: `PingRequest.py` and `PongResponse.py`

`inputs/PingRequest.py`

```py
from stitches_py.resources import field, subfield

@field()
class PingRequest:
    """
    PingRequest
    """
    pass
```

`inputs/PongResponse.py`

```py
from stitches_py.resources import field, subfield

@field()
class PongResponse:
    """
    PongResponse
    """
    pass
```

As you can see in the above code, `stitches-py` utilizes Python annotations to designate resources. Let's now add a subfield to `PingRequest` to demonstate these annotations further.


`inputs/PingRequest.py`

```py
from stitches_py.resources import field, subfield

@field()
class PingRequest:
    """
    PingRequest
    """

    @subfield
    def req_id(self) -> str:
        """ UUID used to track requests. """
        pass
    
    @subfield
    def send_ts(self) -> int:
        """Time (in milliseconds) when the request was sent."""
        pass
```

Keying off the `@subfield` annotation, the `stitches-py` library can infer the field type using Python's type hinting system.

Now let us also add subfields to `PongRequest`.

`inputs/PongResponse.py`

```py
from stitches_py.resources import field, subfield

@field()
class PongResponse:
    """
    PongResponse
    """
    @subfield
    def req_id(self) -> str:
        """ID of the received request."""
        pass

    @subfield
    def recv_ts(self) -> int:
        """Time (in milliseconds) when the request was received."""
        pass
```

Now that we have finished creating our field definitions, we need to register them with the FTGRepo

```bash
./stitches-py ftg register
```

#### Subsytems
Now let's define the functionality of our two subsystems `PingRquester` and `PongResponder`.

```bash
./stitches-py ss create PingRequester --empty
./stitches-py ss create PongResponder --empty

# To see cli help
./stitches-py ss create --help

# List new fields
./stitches-py ss list
```

There should be two new files in the `inputs/` directory: `PingRequester.py` and  `PongResponder.py`

`inputs/PingRequester.py`

```python
import asyncio
from stitches_py.resources import field, subfield, subsystem, ss_interface, ss_thread

@subsystem()
class PingRequester:
    """
    PingRequester
    """
    
    pass
```

`inputs/PongResponder.py`

```python
import asyncio
from stitches_py.resources import field, subfield, subsystem, ss_interface, ss_thread

@subsystem()
class PongResponder:
    """
    PongResponder
    """
    
    pass
```

Next, we use the `@ss_interface` decorator to define interfaces for the subsystems.

`inputs/PingRequester.py`

```python
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
    
    @ss_interface
    def ping(self) -> PingRequest: # Return annotations designate Out Interfaces
        """
        Out interface which sends ping requests.
        """
        req = PingRequest()
        req.req_id = str(uuid4())
        req.send_ts = int(time.time() * 1000) # Convert ts to milliseconds

        return req


    @ss_interface
    def ping_pong(self, resp: PongResponse): # Input annotations designate In Interfaces.
        """
        In interface which receives pong responses generated from ping requests.
        """
        self._logger.info(f'Received pong for ping ({resp.req_id}).')
```

`inputs/PongResponder.py`

```python
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
        resp = PongReponse()
        resp.req_id = req.req_id # Attach the request id for tracking.
        resp.recv_ts = int(time.time() * 1000) # Convert ts to milliseconds

        return resp
```

The `@ss_interface` decorator relies heavily on the Pythons method type-hinting to determine direction and field type. 

Finally, we want ping requests to be send at a certain interval. We can use `@ss_thread` to define background threads for our subsystems.

`inputs/PingRequester.py`

```python
@ss_thread
async def _send_pings(self):
    """
    Thread to send pings at a predefined interval.
    """
    while not self._shutdown_requested: # Flag to detect shutdowns and exit gracefully.
        await asyncio.sleep(5)
        self.ping() # Trigger Out Interface by calling the bound method.
```

Now we can generate the STITCHES interfaces for our `stitches-py` subsystems.

```bash
./stitches-py ss build
```

You can view the output of the compile subsystems in `build/`

To run one of our new subsystems.

```bash
./stitches-py ss run pongresponder.ss.PingRequester
./stitches-py ss run pingrequester.ss.PongResponder
```

*** Note: SSes are not yet configured to exit gracefully. User `CTL+C` to quit.

### Systems of Systems
***Warning: WIP***

Finally we need to define our System of Systems connecting our subsystems.

`inputs/PingPong.py`

```python
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

    @sos_subsystem
    def pinger(self) -> PingRequester:
        """ Subsystem sending ping requests """
        pass


    @sos_subsystem
    def ponger(self) -> PongResponder:
        """ Subsystem replying with pong responses """
        pass


    @sos_connection('pinger', 'ping', 'ponger', 'pong')
    def ping_to_pong(self, msg: PingRequest) -> PingRequest:
        """Route PingRequests from the ping interface on the pinger to ponger. """
        # TODO: Allow for transforms?
        pass


    @sos_connection('ponger', 'pong', 'pinger', 'ping_pong')
    def pong_to_pingpong(self, msg: PongResponse) -> PongResponse:
        """ Route PingRequests from pinger to ponger. """
        # TODO: Allow for transforms?
        pass

```


```bash
./stitches-py sos build
```


#### TLDR
To generate the compiled resources for this tutorial:

```bash
./stitches-py --input-dir tutorials/1_pingpong ftg register
./stitches-py --input-dir examples/1_pingpong ss build
./stitches-py --input-dir examples/1_pingpong sos build pingpong.sos.PingPong
cd build/PingPong
docker-compose up -d
```