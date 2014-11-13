# -*- coding: utf-8 -*-

"""This package analyzes, transforms and optimizes tasty_protocols.

We are relying heavily on the python ast package. We are operating on
abstract syntax trees and using for traversal visitors and transformers.

Frequently used terms in this package
=====================================
    - fqnn = fully qualified node name aka symbol, assigned variable
        - server.a = Unsigned(bitlen=8, val=42) # fqnn = ("server", "a")
        - LENGTH = 32 # fqnn = ("LENGTH",)
        - client.omega[i] # fqnn ("client", "omega", "i")
    - symbol = see fqnn
    - symbol_table = a mapping of a fqnn to metadata: type, bit length, dimensions, line number and column number, etc...

Tasty Validation rules
----------------------
    - operations are only allowed of party attributes attached to same party,
    of combination of attached party attributes and global constants,
    or global constants.
    - lshift augmented assignments aka tasty operator aka '<<=' is only allowed on party attributes attached to different parties.
    - symbols of subclass GarbledType must not be reassigned
    - tasty types must be initialized by keyword arguments, not positional arguments
"""


from tasty.tastyc.analyzation import register_class_for_analyzation
from tasty.tastyc.tastyc import compiler_start

__all__ = ["compiler_start", "register_class_for_analyzation"]
