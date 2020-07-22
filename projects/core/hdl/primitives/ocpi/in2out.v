// This is called from VHDL to do a signal alias without a delta cycle
module in2out(input in_port, output out_port);
  assign out_port = in_port;
endmodule
