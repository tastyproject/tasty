# -*- coding: utf-8 -*-

"""
This module provides socket specializations for object wise sending
and receiving using cPickle
"""

import cPickle as pickle
import socket, time
import struct

from tasty import state

from tasty.protocols.protocol import get_realcost


from tasty.utils import ByteCounter

__all__ = ["ServerObjectSocket", "ClientObjectSocket"]

class ObjectSocket(socket._socketobject):
    """Object socket class

    Socket class extended by methods to send and receive objects.
    """

    def __init__(self, family=socket.AF_INET, socktype=socket.SOCK_STREAM,
        proto=0, _sock=None):
        """Std constructor

        @see: socket.socket
        """

        super(ObjectSocket, self).__init__(family, socktype, proto, _sock)
        self.sizei = struct.calcsize("!I")
        self.send_count = ByteCounter("sender")
        self.recv_count = ByteCounter("receiver")


    def sendobj(self, obj):
        """Pickles and sends objects to a connection and interally counts
        the number of total bytes send.

        @type obj: object
        @param obj: every object which supports the pickle protocol

        @rtype: NoneType
        """
#        w = get_realcost("send-duration")
#        t = time.time()
        if type(obj) == type(None):
            tosend = struct.pack("!I", 0)
            len_data = self.sizei
        else:
            data = pickle.dumps(obj, protocol=2)
            len_data = len(data)
            tosend = struct.pack("!I", len_data) + data
            len_data += self.sizei
#        w.start()
        self.sendall(tosend)
#        w.stop()
        self.send_count(len_data)

    def recvobj(self):
        """Receives pickled objects from a socket and counts
        the received bytes.

        @rtype: object
        """
#        t = time.time()
        recv  = self.recv
        sizei = self.sizei
        l = recv(sizei)
#        w = get_realcost("recv-duration")
        len_bytes = struct.unpack("!I", l)[0]
        if len_bytes == 0:
            obj = None
        else:
#            w.start()
            buf = ""
            len_buffer = 0
            while len_buffer < len_bytes:
                buf +=  recv(len_bytes - len_buffer)
                len_buffer = len(buf)
#            w.stop()
            obj = pickle.loads(buf)
        self.recv_count(len_bytes + sizei)
        return obj


class ServerObjectSocket(ObjectSocket):
    """Server object socket. Opens a server socket on initialization"""

    def __init__(self, host="::", port=0, family=socket.AF_INET6,
        socktype=socket.SOCK_STREAM, proto=0):
        """Std constructor

        @see: socket.socket
        """

        super(ServerObjectSocket, self).__init__(family, socktype, proto)
        self.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.bind((host, port))
        self.listen(1)

    def accept(self):
        """Blocks until a new connection arrives and returns an sock
        and address tuple.

        @rtype: tuple(sock, addr)
        @return: host, adr
        """

        sock, addr = self._sock.accept()
        sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
        return ObjectSocket(_sock=sock), addr


class ClientObjectSocket(ObjectSocket):
    """Client object socket. Opens a client connection on initialization"""

    def __init__(self, host="::1", port=0, family=socket.AF_INET6,
        socktype=socket.SOCK_STREAM, proto=0):
        """Std constructor

        @see: socket.socket
        """

        super(ClientObjectSocket, self).__init__(family, socktype, proto)
        self.connect((host, port))
        self.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
