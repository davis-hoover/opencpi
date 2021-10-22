This directory contains code to support runtime typed data values.
The typing system is roughly based on the IDL/CORBA typing system where there are scalars, structures,
multidimensional arrays of scalars, and (runtime-variable-length single dimension) sequences of scalars
or arrays or structs.
Scalars are numbers of various types and sizes, as well as strings.

And types can be recursive (sequences of arrays of sequences of sequences) etc.

There are these capabilities:

- Data type management, including parsing XML representations of data types.
- Value management where we parse textual values into runtime values and "unparse" values into text.
- A special case of typed scalar-only runtime parameter values, called PValues where variable length arrays
  of typed scalar values are passed to certain high-level functions.
- serialize and deserialize (reader/writer) functions for structures (ordered, named, typed, values) to
  put these values into contiguous binary buffers of data.



