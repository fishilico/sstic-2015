Solution of SSTIC 2015 challenge, in French
===========================================

This repository contains the scripts and other resources I have used to solve
the computer-security challenge of SSTIC 2015, available at
http://communaute.sstic.org/ChallengeSSTIC2015

I am used to write code and README files in English, so even if the report
describing my solution is written in French, every other file would be written
in English.


Dependencies
------------

To be able to successfully build this project, the following software is needed:

* Usual build tools: ``gcc``, ``g++``, ``make``, ``coreutils``...
* Some archive tools: ``tar``, ``unzip``
* Python 2.7 (for scapy) and 3 (tested with 3.4)
* LaTeX, to build the solution PDF
* openssl program to decrypt stages 0, 2 and 4, https://www.openssl.org/
* scapy Python library for stage 3, http://www.secdev.org/projects/scapy/
* Crypto++ C++ library, to decrypt stage 3, http://www.cryptopp.com/
* pillow Python library, for stage 6, http://python-pillow.github.io/

Optional dependencies:

* PyCrypto Python library, to run stage 4 bruteforce code,
  http://www.dlitz.net/software/pycrypto/
* SciTE, to generate script listings (``.inc.tex`` files),
  http://www.scintilla.org/SciTE.html


Build commands
--------------

* To build everything possible in this repository, type::

    make

* To build the solution PDF::

    make solution.pdf

* To build the final image from the inital archive of the challenge::

    make stage6/solution.png
