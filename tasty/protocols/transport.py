# -*- coding: utf-8 -*-

"""Holds protocols essential for tastys transport matters"""

from tasty.protocols import protocol

class Transport(protocol.Protocol):
    """
    Protocol for sending data

    client and server side
    self.args = iterable of objects to send
    """

    name = "Transport"
    def online1(self, args):
        return self.args

    def online2(self, args):
        self.results = tuple(args)
        return None

    client_online_queue = server_online_queue = [online1, online2]

