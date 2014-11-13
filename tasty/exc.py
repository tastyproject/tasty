# -*- coding: utf-8 -*-


class UserWarningOnce(UserWarning):
    """ Use this warning if you want to see this warning just once"""
    pass


class UserWarningRepeated(UserWarning):
    """ Use this warning if you want to see this warning every time warn is called"""
    pass


class MightOverflowWarning(UserWarningRepeated):
    pass


class TastyException(Exception):
    pass


class AnalyzerUnknownNodeTypeError(TastyException, TypeError):
    pass


class GoOutHere(Exception):
    pass


class TastySyntaxError(TastyException, SyntaxError):
    """ Raised if tasty specific syntax errors are found, e.g trying to send an
    obj to the same party, or operations on attributes of different parties.
    """
    pass

class UnknownSymbolError(TastyException):
    """Raised if there is no symbol stored in tastys symbol table"""
    pass


class InternalError(TastyException):
    """ Raises if a case is reached that should be unreachable. This is usually
    a bug in Tasty
    """
    pass


class EvaluateAndRetryError(ValueError):
    """Use this child class of ValueError when a visit happens before the node was not evaluated.
    Evaluate means partial evaluation. There are not enough information to it at the code the exception was raised.
    So the calling code should try to visit the node before retrying whatever he has done before"""
    pass


class UserWarningOnce(UserWarning):
    """ Use This Warning if you want to see a warning """
    pass


class UserWarningRepeated(UserWarning):
    pass


class FqnnError(NotImplementedError):
    pass

class TastyUsageError(Exception):
    pass
