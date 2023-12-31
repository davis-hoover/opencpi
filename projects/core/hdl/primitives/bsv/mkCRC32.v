/*
 * This file is protected by Copyright. Please refer to the COPYRIGHT file
 * distributed with this source distribution.
 *
 * This file is part of OpenCPI <http://www.opencpi.org>
 *
 * OpenCPI is free software: you can redistribute it and/or modify it under the
 * terms of the GNU Lesser General Public License as published by the Free
 * Software Foundation, either version 3 of the License, or (at your option) any
 * later version.
 *
 * OpenCPI is distributed in the hope that it will be useful, but WITHOUT ANY
 * WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
 * A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
 * details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 */

//
// Generated by Bluespec Compiler, version 2012.09.beta1 (build 29570, 2012-09.11)
//
// On Thu Sep 13 03:05:01 UTC 2012
//
// Method conflict info:
// Method: add
// Conflict-free: clear, result, complete
// Conflicts: add
//
// Method: clear
// Conflict-free: add, result, complete
// Conflicts: clear
//
// Method: result
// Conflict-free: add, clear, result, complete
//
// Method: complete
// Conflict-free: add, clear, result
// Conflicts: complete
//
//
// Ports:
// Name                         I/O  size props
// RDY_add                        O     1 const
// RDY_clear                      O     1 const
// result                         O    32
// RDY_result                     O     1 const
// complete                       O    32
// RDY_complete                   O     1 const
// CLK                            I     1 clock
// RST_N                          I     1 reset
// add_data                       I     8
// EN_add                         I     1
// EN_clear                       I     1
// EN_complete                    I     1
//
// No combinational paths from inputs to outputs
//
//

`ifdef BSV_ASSIGNMENT_DELAY
`else
  `define BSV_ASSIGNMENT_DELAY
`endif

`ifdef BSV_POSITIVE_RESET
  `define BSV_RESET_VALUE 1'b1
  `define BSV_RESET_EDGE posedge
`else
  `define BSV_RESET_VALUE 1'b0
  `define BSV_RESET_EDGE negedge
`endif

module mkCRC32(CLK,
	       RST_N,

	       add_data,
	       EN_add,
	       RDY_add,

	       EN_clear,
	       RDY_clear,

	       result,
	       RDY_result,

	       EN_complete,
	       complete,
	       RDY_complete);
  input  CLK;
  input  RST_N;

  // action method add
  input  [7 : 0] add_data;
  input  EN_add;
  output RDY_add;

  // action method clear
  input  EN_clear;
  output RDY_clear;

  // value method result
  output [31 : 0] result;
  output RDY_result;

  // actionvalue method complete
  input  EN_complete;
  output [31 : 0] complete;
  output RDY_complete;

  // signals for module outputs
  wire [31 : 0] complete, result;
  wire RDY_add, RDY_clear, RDY_complete, RDY_result;

  // register rRemainder
  reg [31 : 0] rRemainder;
  wire [31 : 0] rRemainder$D_IN;
  wire rRemainder$EN;

  // remaining internal signals
  wire [31 : 0] IF_IF_IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wg_ETC___d368,
		IF_IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget__ETC___d367,
		IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_ETC___d366,
		IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0__ETC___d365,
		IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CON_ETC___d364,
		IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_ETC___d363,
		IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_rw_ETC___d362,
		rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_rwAdd_ETC___d361,
		remainder__h3146,
		remainder__h3173,
		remainder__h3187,
		remainder__h3214,
		remainder__h3228,
		remainder__h3255,
		remainder__h3269,
		remainder__h3296,
		remainder__h3310,
		remainder__h3337,
		remainder__h3351,
		remainder__h3378,
		remainder__h3392,
		remainder__h3419,
		remainder__h3433,
		remainder__h3460,
		x__h251,
		y__h2373;
  wire [7 : 0] x__h2379;

  // action method add
  assign RDY_add = 1'd1 ;

  // action method clear
  assign RDY_clear = 1'd1 ;

  // value method result
  assign result =
	     { ~rRemainder[0],
	       ~rRemainder[1],
	       ~rRemainder[2],
	       ~rRemainder[3],
	       ~rRemainder[4],
	       ~rRemainder[5],
	       ~rRemainder[6],
	       ~rRemainder[7],
	       ~rRemainder[8],
	       ~rRemainder[9],
	       ~rRemainder[10],
	       ~rRemainder[11],
	       ~rRemainder[12],
	       ~rRemainder[13],
	       ~rRemainder[14],
	       ~rRemainder[15],
	       ~rRemainder[16],
	       ~rRemainder[17],
	       ~rRemainder[18],
	       ~rRemainder[19],
	       ~rRemainder[20],
	       ~rRemainder[21],
	       ~rRemainder[22],
	       ~rRemainder[23],
	       ~rRemainder[24],
	       ~rRemainder[25],
	       ~rRemainder[26],
	       ~rRemainder[27],
	       ~rRemainder[28],
	       ~rRemainder[29],
	       ~rRemainder[30],
	       ~rRemainder[31] } ;
  assign RDY_result = 1'd1 ;

  // actionvalue method complete
  assign complete =
	     { ~rRemainder[0],
	       ~rRemainder[1],
	       ~rRemainder[2],
	       ~rRemainder[3],
	       ~rRemainder[4],
	       ~rRemainder[5],
	       ~rRemainder[6],
	       ~rRemainder[7],
	       ~rRemainder[8],
	       ~rRemainder[9],
	       ~rRemainder[10],
	       ~rRemainder[11],
	       ~rRemainder[12],
	       ~rRemainder[13],
	       ~rRemainder[14],
	       ~rRemainder[15],
	       ~rRemainder[16],
	       ~rRemainder[17],
	       ~rRemainder[18],
	       ~rRemainder[19],
	       ~rRemainder[20],
	       ~rRemainder[21],
	       ~rRemainder[22],
	       ~rRemainder[23],
	       ~rRemainder[24],
	       ~rRemainder[25],
	       ~rRemainder[26],
	       ~rRemainder[27],
	       ~rRemainder[28],
	       ~rRemainder[29],
	       ~rRemainder[30],
	       ~rRemainder[31] } ;
  assign RDY_complete = 1'd1 ;

  // register rRemainder
  assign rRemainder$D_IN =
	     (EN_clear || EN_complete) ? 32'hFFFFFFFF : x__h251 ;
  assign rRemainder$EN = EN_clear || EN_complete || EN_add ;

  // remaining internal signals
  assign IF_IF_IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wg_ETC___d368 =
	     IF_IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget__ETC___d367[31] ?
	       remainder__h3392 :
	       remainder__h3419 ;
  assign IF_IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget__ETC___d367 =
	     IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_ETC___d366[31] ?
	       remainder__h3351 :
	       remainder__h3378 ;
  assign IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_ETC___d366 =
	     IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0__ETC___d365[31] ?
	       remainder__h3310 :
	       remainder__h3337 ;
  assign IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0__ETC___d365 =
	     IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CON_ETC___d364[31] ?
	       remainder__h3269 :
	       remainder__h3296 ;
  assign IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CON_ETC___d364 =
	     IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_ETC___d363[31] ?
	       remainder__h3228 :
	       remainder__h3255 ;
  assign IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_ETC___d363 =
	     IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_rw_ETC___d362[31] ?
	       remainder__h3187 :
	       remainder__h3214 ;
  assign IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_rw_ETC___d362 =
	     rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_rwAdd_ETC___d361[31] ?
	       remainder__h3146 :
	       remainder__h3173 ;
  assign rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_rwAdd_ETC___d361 =
	     rRemainder ^ y__h2373 ;
  assign remainder__h3146 =
	     { rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_rwAdd_ETC___d361[30:26],
	       ~rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_rwAdd_ETC___d361[25],
	       rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_rwAdd_ETC___d361[24:23],
	       ~rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_rwAdd_ETC___d361[22:21],
	       rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_rwAdd_ETC___d361[20:16],
	       ~rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_rwAdd_ETC___d361[15],
	       rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_rwAdd_ETC___d361[14:12],
	       ~rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_rwAdd_ETC___d361[11:9],
	       rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_rwAdd_ETC___d361[8],
	       ~rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_rwAdd_ETC___d361[7:6],
	       rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_rwAdd_ETC___d361[5],
	       ~rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_rwAdd_ETC___d361[4:3],
	       rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_rwAdd_ETC___d361[2],
	       ~rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_rwAdd_ETC___d361[1:0],
	       1'd1 } ;
  assign remainder__h3173 =
	     { rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_rwAdd_ETC___d361[30:0],
	       1'd0 } ;
  assign remainder__h3187 =
	     { IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_rw_ETC___d362[30:26],
	       ~IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_rw_ETC___d362[25],
	       IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_rw_ETC___d362[24:23],
	       ~IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_rw_ETC___d362[22:21],
	       IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_rw_ETC___d362[20:16],
	       ~IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_rw_ETC___d362[15],
	       IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_rw_ETC___d362[14:12],
	       ~IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_rw_ETC___d362[11:9],
	       IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_rw_ETC___d362[8],
	       ~IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_rw_ETC___d362[7:6],
	       IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_rw_ETC___d362[5],
	       ~IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_rw_ETC___d362[4:3],
	       IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_rw_ETC___d362[2],
	       ~IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_rw_ETC___d362[1:0],
	       1'd1 } ;
  assign remainder__h3214 =
	     { IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_rw_ETC___d362[30:0],
	       1'd0 } ;
  assign remainder__h3228 =
	     { IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_ETC___d363[30:26],
	       ~IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_ETC___d363[25],
	       IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_ETC___d363[24:23],
	       ~IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_ETC___d363[22:21],
	       IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_ETC___d363[20:16],
	       ~IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_ETC___d363[15],
	       IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_ETC___d363[14:12],
	       ~IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_ETC___d363[11:9],
	       IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_ETC___d363[8],
	       ~IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_ETC___d363[7:6],
	       IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_ETC___d363[5],
	       ~IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_ETC___d363[4:3],
	       IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_ETC___d363[2],
	       ~IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_ETC___d363[1:0],
	       1'd1 } ;
  assign remainder__h3255 =
	     { IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CONCAT_ETC___d363[30:0],
	       1'd0 } ;
  assign remainder__h3269 =
	     { IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CON_ETC___d364[30:26],
	       ~IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CON_ETC___d364[25],
	       IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CON_ETC___d364[24:23],
	       ~IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CON_ETC___d364[22:21],
	       IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CON_ETC___d364[20:16],
	       ~IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CON_ETC___d364[15],
	       IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CON_ETC___d364[14:12],
	       ~IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CON_ETC___d364[11:9],
	       IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CON_ETC___d364[8],
	       ~IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CON_ETC___d364[7:6],
	       IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CON_ETC___d364[5],
	       ~IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CON_ETC___d364[4:3],
	       IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CON_ETC___d364[2],
	       ~IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CON_ETC___d364[1:0],
	       1'd1 } ;
  assign remainder__h3296 =
	     { IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0_CON_ETC___d364[30:0],
	       1'd0 } ;
  assign remainder__h3310 =
	     { IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0__ETC___d365[30:26],
	       ~IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0__ETC___d365[25],
	       IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0__ETC___d365[24:23],
	       ~IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0__ETC___d365[22:21],
	       IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0__ETC___d365[20:16],
	       ~IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0__ETC___d365[15],
	       IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0__ETC___d365[14:12],
	       ~IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0__ETC___d365[11:9],
	       IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0__ETC___d365[8],
	       ~IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0__ETC___d365[7:6],
	       IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0__ETC___d365[5],
	       ~IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0__ETC___d365[4:3],
	       IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0__ETC___d365[2],
	       ~IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0__ETC___d365[1:0],
	       1'd1 } ;
  assign remainder__h3337 =
	     { IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_0__ETC___d365[30:0],
	       1'd0 } ;
  assign remainder__h3351 =
	     { IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_ETC___d366[30:26],
	       ~IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_ETC___d366[25],
	       IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_ETC___d366[24:23],
	       ~IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_ETC___d366[22:21],
	       IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_ETC___d366[20:16],
	       ~IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_ETC___d366[15],
	       IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_ETC___d366[14:12],
	       ~IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_ETC___d366[11:9],
	       IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_ETC___d366[8],
	       ~IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_ETC___d366[7:6],
	       IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_ETC___d366[5],
	       ~IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_ETC___d366[4:3],
	       IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_ETC___d366[2],
	       ~IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_ETC___d366[1:0],
	       1'd1 } ;
  assign remainder__h3378 =
	     { IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget_BIT_ETC___d366[30:0],
	       1'd0 } ;
  assign remainder__h3392 =
	     { IF_IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget__ETC___d367[30:26],
	       ~IF_IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget__ETC___d367[25],
	       IF_IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget__ETC___d367[24:23],
	       ~IF_IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget__ETC___d367[22:21],
	       IF_IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget__ETC___d367[20:16],
	       ~IF_IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget__ETC___d367[15],
	       IF_IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget__ETC___d367[14:12],
	       ~IF_IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget__ETC___d367[11:9],
	       IF_IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget__ETC___d367[8],
	       ~IF_IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget__ETC___d367[7:6],
	       IF_IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget__ETC___d367[5],
	       ~IF_IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget__ETC___d367[4:3],
	       IF_IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget__ETC___d367[2],
	       ~IF_IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget__ETC___d367[1:0],
	       1'd1 } ;
  assign remainder__h3419 =
	     { IF_IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wget__ETC___d367[30:0],
	       1'd0 } ;
  assign remainder__h3433 =
	     { IF_IF_IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wg_ETC___d368[30:26],
	       ~IF_IF_IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wg_ETC___d368[25],
	       IF_IF_IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wg_ETC___d368[24:23],
	       ~IF_IF_IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wg_ETC___d368[22:21],
	       IF_IF_IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wg_ETC___d368[20:16],
	       ~IF_IF_IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wg_ETC___d368[15],
	       IF_IF_IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wg_ETC___d368[14:12],
	       ~IF_IF_IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wg_ETC___d368[11:9],
	       IF_IF_IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wg_ETC___d368[8],
	       ~IF_IF_IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wg_ETC___d368[7:6],
	       IF_IF_IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wg_ETC___d368[5],
	       ~IF_IF_IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wg_ETC___d368[4:3],
	       IF_IF_IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wg_ETC___d368[2],
	       ~IF_IF_IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wg_ETC___d368[1:0],
	       1'd1 } ;
  assign remainder__h3460 =
	     { IF_IF_IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wg_ETC___d368[30:0],
	       1'd0 } ;
  assign x__h2379 =
	     { add_data[0],
	       add_data[1],
	       add_data[2],
	       add_data[3],
	       add_data[4],
	       add_data[5],
	       add_data[6],
	       add_data[7] } ;
  assign x__h251 =
	     IF_IF_IF_IF_IF_IF_IF_rRemainder_XOR_rwAddIn_wg_ETC___d368[31] ?
	       remainder__h3433 :
	       remainder__h3460 ;
  assign y__h2373 = { x__h2379, 24'd0 } ;

  // handling of inlined registers

  always@(posedge CLK)
  begin
    if (RST_N == `BSV_RESET_VALUE)
      begin
        rRemainder <= `BSV_ASSIGNMENT_DELAY 32'hFFFFFFFF;
      end
    else
      begin
        if (rRemainder$EN)
	  rRemainder <= `BSV_ASSIGNMENT_DELAY rRemainder$D_IN;
      end
  end

  // synopsys translate_off
  `ifdef BSV_NO_INITIAL_BLOCKS
  `else // not BSV_NO_INITIAL_BLOCKS
  initial
  begin
    rRemainder = 32'hAAAAAAAA;
  end
  `endif // BSV_NO_INITIAL_BLOCKS
  // synopsys translate_on
endmodule  // mkCRC32

