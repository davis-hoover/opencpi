%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% this file was generated by docGen.py
% editing this file is NOT recommended
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
\iffalse
This file is protected by Copyright. Please refer to the COPYRIGHT file
distributed with this source distribution.

This file is part of OpenCPI <http://www.opencpi.org>

OpenCPI is free software: you can redistribute it and/or modify it under the
terms of the GNU Lesser General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

OpenCPI is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License along
with this program. If not, see <http://www.gnu.org/licenses/>.
\fi

\subsection*{complex\_mixer.hdl}
\begin{scriptsize}
\begin{longtable}{|p{\dimexpr0.1\linewidth-2\tabcolsep\relax}
                  |p{\dimexpr0.15\linewidth-2\tabcolsep\relax}
                  |p{\dimexpr0.075\linewidth-2\tabcolsep\relax}
                  |p{\dimexpr0.075\linewidth-2\tabcolsep\relax}
                  |p{\dimexpr0.1\linewidth-2\tabcolsep\relax}
                  |p{\dimexpr0.1\linewidth-2\tabcolsep\relax}
                  |p{\dimexpr0.1\linewidth-2\tabcolsep\relax}
                  |p{\dimexpr0.15\linewidth-2\tabcolsep\relax}
                  |p{\dimexpr0.075\linewidth-2\tabcolsep\relax}
                  |p{\dimexpr0.075\linewidth-2\tabcolsep\relax}|}
\hline
\rowcolor{blue}
Type & Name & Producer & Protocol & Optional & DataWidth & Clock & ClockDirection & WorkerEOF & InsertEOM
\\
\hline
StreamInterface & in & False & iqstream\_protocol & False & 32 & (control clock) & - & False & False\\

\hline
StreamInterface & out & True & iqstream\_protocol & False & 32 & (control clock) & - & False & True\\

\hline
\end{longtable}
\end{scriptsize}
