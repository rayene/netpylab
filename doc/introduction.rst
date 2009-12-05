Introduction
============

==============
About NetPyLab
==============

NetPyLab is an IP network emulator and simulator written in Python_.  It allows 
to simulate/emulate a wide variety of network conditions and network protocols
on a single computer. 

.. _Python: http://www.python.org/

It relies on Scapy_ to sniff, forge and inject packets into real networks. 
Therefore, it can be used to communicate with real-world applications and 
servers (e.g., ping google with a delay of five seconds). In addition, it can 
be used for real-world simulations

.. _Scapy: http://www.secdev.org/projects/scapy/

=====================
NetPyLab for Research
=====================


----------------------------------------------------------------
NetPyLab for Behavior Assessment Under "Hard" Network Conditions
----------------------------------------------------------------

NetPyLab is designed to allow controlled, reproducible experiments with 
network performance sensitive/adaptive applications and control protocols in a 
simple laboratory setting.

NetPyLab can reproduce critical end-to-end performance characteristics imposed 
by various wide area network and wireless network situations :

* Losses and delays (Congestion, Handovers, etc.,)
* Asymmetric bandwidth situations (e.g., xDsl)

It can use real GPS traces to simulate the mobility of network devices and 
delay/drop packets accordingly.

---------------------------------
NetPyLab for Protocol Prototyping
---------------------------------

NetPyLab is great for a quick and easy prototyping of network protocols.
Just have a look on the protocols already proposed in the `layers` folder so
that you don't start from scratch. 

You can stress you code by injecting malformed, unsequenced and delayed
packets and see how it reacts.

When your code is mature enough, you can move smoothly to a production-quality
implementation and test it using the NetPyLab prototype in emulation mode.


======================
NetPyLab for Education
======================

===========================
NetPyLab for Demonstrations
===========================


=======================
NetPyLab and the Python
=======================

I chose Python_ because it is an extraordinary toolbox that is easy to learn
and makes coding a real pleasure. Thanks Guido_ for this great tool ! 

NetPyLab is 100% Python_. Even the simulation scripts and the configuration 
files are written in Python_. If you decide to use it, you have only one 
language to learn with a very even learning curve.

.. _Guido: http://www.python.org/~guido/

==========
Quick Demo
==========


