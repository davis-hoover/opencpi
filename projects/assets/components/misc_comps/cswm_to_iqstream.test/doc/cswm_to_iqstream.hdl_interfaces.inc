%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% this file was generated by docGen.py
% editing this file is NOT recommended
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\subsection*{cswm\_to\_iqstream.hdl}
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
StreamInterface & in & False & ComplexShortWithMetadata-prot & False & IN\_PORT\_DATA\_WIDTH & - & in & False & False\\

\hline
StreamInterface & out & True & iqstream\_protocol & False & OUT\_PORT\_DATA\_WIDTH & in & - & False & False\\

\hline
\end{longtable}
\end{scriptsize}
