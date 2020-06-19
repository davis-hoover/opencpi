%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% this file was generated by docGen.py
% this file is intended to be edited
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\section*{Summary - \Comp}
% Make table whose width is equal to which will be used for text
% wrapping, split into 2 equal columns
\begin{longtable}{|p{\dimexpr0.5\textwidth-2\tabcolsep\relax}
                  |p{\dimexpr0.5\textwidth-2\tabcolsep\relax}|}
  \hline
  \rowcolor{blue}
  & \\
  \hline
  Name              & \comp \\
  \hline
  Latest Version    &  \docVersion (release date TBD) \\
  \hline
  Worker Type       &  Application Worker \\
  \hline
  Component Library &  ocpi.assets.misc\_comps \\
  \hline
  Workers           & \comp.hdl \\
  \hline
  Tested Platforms  &  xsim, isim, ZedBoard(PL) \\
  \hline
\end{longtable}


\begin{center}
	\textit{\textbf{Revision History}}
		\begin{table}[H]
		\label{table:revisions} % Add "[H]" to force placement of table
			\begin{tabularx}{\textwidth}{|c|X|l|}
			\hline
			\rowcolor{blue}
			\textbf{Revision} & \textbf{Description of Change} & \textbf{Date} \\
		    \hline
		    v\docVersion & Initial Release & TBD \\
			\end{tabularx}
		\end{table}
	\end{center}

\section*{Functionality}
The \comp \ serves as a testbench for the \verb+bits+ cdc primitive. The \verb+bits+ primitive synchronizes a bus of bits using single-bit multi-register synchronizers. The \verb+bits+ primitive's \texttt{width} generic sets how many  single-bit multi-register synchronizers to use.
Coherency among the bus of bits is not guaranteed and is intended for uses cases where bits need to be synchronized but data coherency doesn't matter.
An example use case of the \verb+bits+ primitive is using it for status bits for unrelated conditions. \\ \\
The worker generates data and sends the data through the bits synchronizer. The output of the synchronizer is sent to worker's output port.

\section*{Worker Implementation Details}
The \comp \ worker instantiates the \verb+bits+ primitive with the input and output being 4 bits wide. The worker uses 4 LFSRs with each one having the same polynomial
but different seeds. The bit shifted out from each LFSR is then used as the input to the \verb+bits+ primitive. Once the input signal has crossed into the destination clock domain it is stored in a FIFO until the worker's output port is ready for the data. The FIFO is used because the data is sent only once and also used to mitigate synchronizing the backpressure from the output port to the LFSRs. \\ \\
The \texttt{src\_clk\_hz} and \texttt{dst\_clk\_hz} parameter properties are used to define the source and destination domain clock frequencies. \\ \\
A clock generator is used to generate the clocks for the source and destination clock domains when the source and destination clock domains are different. \\ \\
\textbf{Fast clock domain to slow clock domain}: \\
When the source clock frequency is faster than destination clock frequency, the destination domain reset signal is sent through a reset synchronizer to synchronize it to the source domain. The source domain uses the sychronized reset to enable a advance\_counter module that outputs a signal to enable the LFSRs. It is used to ensure that the minimum input signal width to the \verb+bits+ primitive is 2x the period of the destination clock and they are seperated by 2x src\_clk cycles to ensure proper crossing of the CDC boundary. See \url{http://www.sunburst-design.com/papers/CummingsSNUG2008Boston_CDC.pdf} - Section 4.4 and \url{https://m.eet.com/media/1137372/17561-310388.pdf} for more information on the 2x requirement. The FIFO is enabled when the destination clock domain has come out of reset. \\ \\
\textbf{Slow clock domain to fast clock domain}: \\
When the source clock frequency is slower than the destination clock frequency, the LFSRs are enabled when the source domain has come out of reset. The source domain reset signal is sent through a reset synchronizer to synchronize it to the destination domain and is used to enable the FIFO. \\ \\
\textbf{Same clock domain}: \\
When the source clock frequency is equal to the destination clock frequency, the destination domain reset signal is sent through a reset synchronizer to synchronize it to the source domain. The source domain uses the sychronized reset to enable a advance\_counter. The source domain reset signal is sent through a reset synchronizer to synchronize it to the destination domain and is used to enable the FIFO. 


\section*{Block Diagrams}
\subsection*{Top level}
\begin{center}
\begin{tikzpicture}[% List of styles applied to all, to override specify on a case-by-case
					every node/.style={
						align=center,  		% use this so that the "\\" for line break works
						minimum size=1.5cm	% creates space above and below text in rectangle
						},
					every edge/.style={draw,thick}
					]
\node[rectangle,ultra thick,draw=black,fill=blue, minimum width=5 cm](R2){Parameter Properties:\\ \verb+src_clk_hz+ \\ \verb+dst_clk_hz+ \\ \verb+num_input_samples+ \\ \\ \comp \\ \\ };
\node[rectangle,draw=white,fill=white](R3)[right= of R2]{``out'' \\ Data};
\path[->]
(R2)edge []     node [] {} (R3)
;
\end{tikzpicture}
\end{center}\pagebreak

%\subsection*{State Machine}
%\begin{flushleft}
%\end{flushleft}

\section*{Source Dependencies}
\subsection*{\comp.hdl}
\begin{itemize}
		\item assets/components/misc\_comps/\comp.hdl/\comp.vhd
	        \item core/hdl/primitives/cdc/bits.vhd
		\item core/hdl/primitives/cdc/cdc\_pkg.vhd
	\end{itemize}

\begin{landscape}
  \input{component_spec_properties.inc} % it is recommended to NOT remove this line

  \input{worker_properties.inc} % it is recommended to NOT remove this line

  \input{component_ports.inc} % it is recommended to NOT remove this line

  \input{worker_interfaces.inc} % it is recommended to NOT remove this line
\end{landscape}

\section*{Data Timing and Signals}
The \comp \ worker uses the clock from the Control Plane as input to the clock generator. The output of the clock generator is used to drive the output port clock.

\section*{Performance and Resource Utilization}
%\subsubsection*{\comp.hdl}

\section*{Test and Verification}
There are files used to validate the data the \comp \ worker sends. The files used in the verification were created from the output of the unit test when running the unit test in simulation and contain the expected output data when there is no metastability. Since there might or might not be a perfect match of the output data to the expected output data when running the tests in hardware due to 
metastability or phase offset, the output data is correlated with the expected output data. If there is at least a 0.7 positive Pearson product-moment correlation coefficient, then test case is considered passing. This correlation is only used when running the unit test on hardware. If the test are run in simulation, the output data is compared with expected output data. If the they match exactly, then test case is considered passing.