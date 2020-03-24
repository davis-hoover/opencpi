
/*
  This file is included to define an AXI interface package, based on some parameters.
  We use the AW, W, B, AR, R channels per the AXI spec.
  We define the A pseudo-channel as the globalsignal channel since the AXI spec uses the A prefix 
  for these global signals.

  Parameters:
    NAME the name of this interface and the name of the package which will be in the axi library
    ADDR_WIDTH applies to AR and AW channels
    ID_WIDTH applies to AR, AW, B, R channels (do we need different onces for 
    DATA_WIDTH applies to the W, and R channels
    CLOCK_FROM_MASTER says the master drives the clock as opposed to the slave
    RESET_FROM_MASTER says the master drives the reset as opposed to the slave
    AXI4 set to non-zero enables the AXI 4 signals and widths, otherwise AXI3 defaults are used
    USER_WIDTH is the width of the AXI4 USER signals for all channels unless overridden by:
    USER_WIDTH_<channel> is the width of the AXI4 USER signal for a specific channel
    The USER_WIDTH signals can be set to 0 to suppress them even if AXI4 is set.
*/
#ifndef USER_WIDTH
#define USER_WIDTH 4
#endif
#ifndef USER_WIDTH_AW
#define USER_WIDTH_AW USER_WIDTH
#endif
#ifndef USER_WIDTH_W
#define USER_WIDTH_W USER_WIDTH
#endif
#ifndef USER_WIDTH_B
#define USER_WIDTH_B USER_WIDTH
#endif
#ifndef USER_WIDTH_AR
#define USER_WIDTH_AR USER_WIDTH
#endif
#ifndef USER_WIDTH_R
#define USER_WIDTH_R USER_WIDTH
#endif
#if AXI4
#define LEN_WIDTH 8
#else
#define LEN_WIDTH 4
#endif
#define CPP_CAT_(a,b) a##b
#define CPP_CAT(a,b) CPP_CAT_(a,b)
#define CONTROL_NAME CPP_CAT(axi2cp_,NAME)
#define SDP_NAME CPP_CAT(sdp2axi_,NAME)

library IEEE; use IEEE.std_logic_1164.all, ieee.numeric_std.all;
library sdp, platform, ocpi; use ocpi.types.all;
package NAME is
  subtype axi_id_t is std_logic_vector(ID_WIDTH-1 downto 0);
  ------------------------------------------------------------
  -- The global signals, which from a prefix point of view is called the A channel
  -- Which of CLK and RESETn is driven by which side varies
#if CLOCK_FROM_MASTER || RESET_FROM_MASTER
  type a_m2s_t is record
#if CLOCK_FROM_MASTER
    CLK : std_logic;
#endif
#if RESET_FROM_MASTER
    RESETn : std_logic;
#endif
  end record a_m2s_t;
#endif
#if !CLOCK_FROM_MASTER || !RESET_FROM_MASTER
  type a_s2m_t is record
#if !CLOCK_FROM_MASTER
    CLK : std_logic;
#endif
#if !RESET_FROM_MASTER
    RESETn : std_logic;
#endif
  end record a_s2m_t;
#endif
  ------------------------------------------------------------
  -- The write address channel, a.k.a. the AW channel
  type aw_m2s_t is record
    ID     : axi_id_t;
    ADDR   : std_logic_vector(ADDR_WIDTH-1 downto 0);
    LEN    : std_logic_vector((LEN_WIDTH)-1 downto 0);
    SIZE   : std_logic_vector(2 downto 0);
    BURST  : std_logic_vector(1 downto 0);
    LOCK   : std_logic_vector(1 downto 0);
    CACHE  : std_logic_vector(3 downto 0);
    PROT   : std_logic_vector(2 downto 0);
    VALID  : std_logic;
    #if AXI4
    QOS    : std_logic_vector(3 downto 0);
    REGION : std_logic_vector(3 downto 0);
    #if USER_WIDTH_AW
    USER   : std_logic_vector(USER_WIDTH_AW-1 downto 0);
    #endif
    #endif
  end record aw_m2s_t;
  type aw_s2m_t is record
    READY : std_logic;
  end record aw_s2m_t;

  -- The write data channel, a.k.a. the W channel
  type w_m2s_t is record
#if !AXI4
    ID     : axi_id_t;
#endif
    DATA   : std_logic_vector(DATA_WIDTH-1 downto 0);
    STRB   : std_logic_vector((DATA_WIDTH/8)-1 downto 0);
    LAST   : std_logic;
    VALID  : std_logic;
    #if AXI4 && USER_WIDTH_W
    USER   : std_logic_vector(USER_WIDTH_W-1 downto 0);
    #endif
  end record w_m2s_t;
  type w_s2m_t is record
    READY : std_logic;
  end record w_s2m_t;

  -- The write response channel, a.k.a. the B channel
  type b_m2s_t is record
    READY : std_logic;
  end record b_m2s_t;
  type b_s2m_t is record
    ID     : axi_id_t;
    RESP   : std_logic_vector(1 downto 0);
    VALID  : std_logic;
    #if AXI4 && USER_WIDTH_B
    USER   : std_logic_vector(USER_WIDTH_B-1 downto 0);
    #endif
  end record b_s2m_t;

  ------------------------------------------------------------
  -- The read address channel, a.k.a. the AR channel
  type ar_m2s_t is record
    ID     : axi_id_t;
    ADDR   : std_logic_vector(ADDR_WIDTH-1 downto 0);
    LEN    : std_logic_vector((LEN_WIDTH)-1 downto 0);
    SIZE   : std_logic_vector(2 downto 0);
    BURST  : std_logic_vector(1 downto 0);
    LOCK   : std_logic_vector(1 downto 0);
    CACHE  : std_logic_vector(3 downto 0);
    PROT   : std_logic_vector(2 downto 0);
    VALID  : std_logic;
    #if AXI4
    QOS    : std_logic_vector(3 downto 0);
    REGION : std_logic_vector(3 downto 0);
    #if USER_WIDTH_AR
    USER   : std_logic_vector(USER_WIDTH_AR-1 downto 0);
    #endif
    #endif
  end record ar_m2s_t;
  type ar_s2m_t is record
    READY : std_logic;
  end record ar_s2m_t;

  -- The read data channel, a.k.a. the R channel
  type r_m2s_t is record
    READY : std_logic;
  end record r_m2s_t;
  type r_s2m_t is record
    ID     : axi_id_t;
    DATA   : std_logic_vector(DATA_WIDTH-1 downto 0);
    RESP   : std_logic_vector(1 downto 0);
    LAST   : std_logic;
    VALID  : std_logic;
    #if AXI4 && USER_WIDTH_R
    USER   : std_logic_vector(USER_WIDTH_R-1 downto 0);
    #endif
  end record r_s2m_t;

  -- The bundles of signals m2s, and s2m
  type axi_m2s_t is record
#if CLOCK_FROM_MASTER || RESET_FROM_MASTER
    a  : a_m2s_t;
#endif
    aw : aw_m2s_t;
    ar : ar_m2s_t;
    w : w_m2s_t;
    r : r_m2s_t;
    b : b_m2s_t;
  end record axi_m2s_t;
  type axi_m2s_array_t is array (natural range <>) of axi_m2s_t;
  type axi_s2m_t is record
#if !CLOCK_FROM_MASTER || !RESET_FROM_MASTER
    a  : a_s2m_t;
#endif
    aw : aw_s2m_t;
    ar : ar_s2m_t;
    w : w_s2m_t;
    r : r_s2m_t;
    b : b_s2m_t;
  end record axi_s2m_t;
  type axi_s2m_array_t is array (natural range <>) of axi_s2m_t;

  ------------------------------------------------------------
  -- The control plane adaptation for this interface
  component CONTROL_NAME is
    port(
      clk     : in std_logic;
      reset   : in bool_t;
      axi_in  : in  axi_m2s_t;
      axi_out : out axi_s2m_t;
      cp_in   : in  platform.platform_pkg.occp_out_t;
      cp_out  : out platform.platform_pkg.occp_in_t
      );
  end component CONTROL_NAME;

  ------------------------------------------------------------
  -- The data plane adaptation for this interface
  component SDP_NAME is
    generic(
      ocpi_debug : boolean;
      sdp_width  : natural);
    port(
      clk          : in  std_logic;
      reset        : in  bool_t;
      sdp_in       : in  sdp.sdp.s2m_t;
      sdp_in_data  : in  dword_array_t(0 to sdp_width-1);
      sdp_out      : out sdp.sdp.m2s_t;
      sdp_out_data : out dword_array_t(0 to sdp_width-1);
      axi_in       : in  axi_s2m_t;
      axi_out      : out axi_m2s_t;
      axi_error    : out bool_t;
      dbg_state    : out ulonglong_t;
      dbg_state1   : out ulonglong_t;
      dbg_state2   : out ulonglong_t
     );
  end component SDP_NAME;
end package NAME;

