Blaeu, creating measurements on RIPE Atlas probes
=================================================

This is a set of `Python <https://www.python.org/>`__ programs to start
distributed Internet measurements on the network of `RIPE Atlas
probes <https://atlas.ripe.net/>`__, and to analyze their results.

For installation, you can use usual Python tools, for instance:

::

    pip3 install blaeu

Usage requires a RIPE Atlas API key (which itself requires a RIPE
account), and RIPE Atlas credits. If you don't have a RIPE account,
`register first <https://access.ripe.net/>`__. Once you have an account,
`create a key <https://atlas.ripe.net/keys/>`__ and put it in
``~/.atlas/auth``. If you don't have Atlas credits, host a probe,or
become a
`LIR <https://www.ripe.net/manage-ips-and-asns/resource-management/faq/independent-resources/phase-three/what-is-a-local-internet-registry-lir>`__
or ask a friend.

You can then use the four programs (``-h`` will give you a complete list
of their options):

-  ``blaeu-reach target-IP-address ̀ (test reachability of the target, like``\ ping\`)
-  ``blaeu-traceroute target-IP-address ̀ (like``\ traceroute\`)
-  \`blaeu-resolve name ̀ (use the DNS to resolve the name)
-  ``blaeu-cert name`` (display the PKIX certificate)

You may also be interested by `my article at RIPE
Labs <https://labs.ripe.net/Members/stephane_bortzmeyer/using-ripe-atlas-to-debug-network-connectivity-problems>`__,
although the tools' installation method and names are now different.

Blaeu requires Python 3.

Note that `the old
version <https://github.com/RIPE-Atlas-Community/ripe-atlas-community-contrib>`__
ran on Python 2 but is no longer maintained.

Name
----

It comes from the `famous Dutch
cartographer <https://en.wikipedia.org/wiki/Willem_Blaeu>`__.

Reference site
--------------

`On FramaGit <https://framagit.org/bortzmeyer/blaeu>`__

Author
------

Stéphane Bortzmeyer stephane+frama@bortzmeyer.org
