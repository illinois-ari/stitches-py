from stitches_py.resources import field, Field, subfield, subsystem, Subsystem


@field()
class FooField:

    @subfield
    def IntSF(self) -> int:
        """
        Integer subfield
        """
        pass