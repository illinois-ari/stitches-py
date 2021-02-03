from stitches_py.resources import field, Field, subfield, subsystem, Subsystem


@field()
class BarField:

    @subfield
    def StringSF(self) -> str:
        """
        String subfield
        """
        pass


@subsystem()
class BarSS:
    pass