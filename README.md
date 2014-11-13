Tasty Documentation
===================

Toolbox for Automatic Secure Two-partY computation

Update 11/2014: This project is not maintained since 2010, skoegl has cleaned up the code base for lib and python version regressions as far as possible. Patches or merge requests are more than welcome :)

 
Welcome to Tasty....

Tool Overview
-------------

A normal workflow consists of creating a tasty protocol environment, customizing the protocol, running and analzing it.

    - tasty_init = Creates a default tasty protocol environment, accepts options
    - tasty = the main tool for running and benchmarking tasty protocols, accepts many options
    - tasty_post = our tool for post processing and visualizing tasty protocol costs, benchmarking results, and generates graphs, etc...

Workflow
--------

First of all you want to create a tasty protocol environment, which consists of a directory containing some important files.
Tasty expects a well defined environment structure. A config file and a tasty protocol file and optionally an analyzation file.
You can create a new protocol environment by copy and paste or with the script 'tasty_init'::

    tasty_init mytest

What you will get::

    desktop implementation # ls -l mytest
    total 12
    -rw-r--r-- 1 root root 124 Nov 19 13:24 protocol.ini
    -rw-r--r-- 1 root root 185 Nov 19 13:24 protocol.py

 - protocol.ini : provides you configuration options.
 - protocol.py : the actual script file for protocol implementation.

The name 'protocol.py' is the default one, but you can also put as many protocol
files as you want inside the tasty protocol environment, but then you must
provide the intended file as flag argument when using tasty.

Tasty expects a procedure with one of two predefined signatures inside the protocol file.
The signature of normal protocols::

def procedure_name(client_party_name, server_name): -> None
    pass

The signature of driven protocols::

def procedure_name(client_party_name, server_fqnn, params_name): -> None
    pass


Tasty Syntax
============


Tasty Types
-----------

    - Signed
    - Unsigned
    - Modular
    - Homomorphic
    - Garbled
    - SignedVec
    - UnsignedVec
    - HomomorphicVec
    - GarbledVec

Theses types must be attached to one of client or server parties. You can also
declare and use global (unattachted) constants of python types int or long.

Attribute/Variable Usage
------------------------

Attribute Initialization and manual input::

    # normal initialization
    client.a = Signed(bitlen=8, val=23)

    # terminal input
    client.b = Signed(bitlen=8).input(desc="usefull description displayed on terminal")

    # in this example provide 6 values, and access them with client.items
    # Each one is a 2-item tuple with the input label and the corresponding value
    server.c = SignedVec(bitlen=8, dim=4).input(src=driver, desc="c")


Attribute Encryption::

    client.ha = Homomorphic(val=server.a)

Send data aka Using the tasty operator::

    server.ha <<= client.ha

Encrypt and send value from server to client::

    client.hb <<= Homomorphic(val=server.b)

Decrypting::

    client.a2 = Signed(val=client.ha)

getting the output

    client.a2.output(desc="client.a2")

Statements
----------

    - Binary operations +-*/
    - Unary operations +-
    - dot product

