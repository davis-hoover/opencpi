
CMA Region Memory Allocation Warning from the Linux Kernel Driver
-----------------------------------------------------------------

.. This section is a snippet since all the GSGs use it. Tex snippets are in the opencpi installation at doc/tex/snippets/.

The OpenCPI Linux kernel module driver will attempt to make use of
the CMA region for direct memory access if it is available.
If you make a lot of memory allocations, you may receive
the following kernel message:

.. code-block::
   
   alloc_contig_range test_pages_isolated([memory-start], [memory-end]) failed

Although this message is a kernel warning, it does not indicate that a memory
allocation failure has occurred, only that the CMA engine could not
allocate memory on the first pass. The driver's default behavior is to make
a second pass and if that succeeds, you should not see any further error
messages. This message cannot be suppressed but it can be safely ignored.
An actual allocation failure will generate unambiguous error messages.
