#!/bin/sh

# Encapsulate ocpihdl wread, wwrite, radmin, and wadmin
read_worker_register()
{
  WORKER_INDEX=$1
  REG_OFFSET=$2
  NUM_BYTES=$3

  ocpihdl wread  $WORKER_INDEX $REG_OFFSET/$NUM_BYTES 1

}

# Encapsulate ocpihdl wwrite
write_worker_register()
{
  WORKER_INDEX=$1
  REG_OFFSET=$2
  NUM_BYTES=$3
  WRITE_DATA=$4

  ocpihdl wwrite $WORKER_INDEX $REG_OFFSET/$NUM_BYTES $WRITE_DATA

}

# Encapsulate ocpihdl radmin
read_admin_register()
{
  REG_OFFSET=$1
  NUM_BYTES=$2

  ocpihdl radmin  $REG_OFFSET/$NUM_BYTES

}

# Encapsulate ocpihdl wadmin
write_admin_register()
{
  REG_OFFSET=$1
  NUM_BYTES=$2
  WRITE_DATA=$3

  ocpihdl wadmin $REG_OFFSET/$NUM_BYTES $WRITE_DATA

}

# Create constants to keep the script more readeable/understandable
PLATFORM_INDEX=0
SDP_SEND_INDEX=3

# <-----------------------------
LENGTH_ONE=1
LENGTH_TWO=2
LENGTH_FOUR=4
LENGTH_EIGHT=8

# <-----------------------------
# Property register offsets
MEMORY_BYTES_OFFSET=0
SDP_ID_OFFSET=4
SDP_WIDTH_OFFSET=6

# <-----------------------------
# Admin register offsets
UUID_OFFSET=0
SCRATCH_20=0x20
SCRATCH_24=0x24

# <-----------------------------
# Read the following property registers to verify read access:
# <-----------------------------
# sdp_width (1-byte)
read_worker_register $SDP_SEND_INDEX $SDP_WIDTH_OFFSET $LENGTH_ONE

# sdp_id (2-bytes)
read_worker_register $SDP_SEND_INDEX $SDP_ID_OFFSET $LENGTH_TWO

# memory_bytes (4-bytes)
read_worker_register $SDP_SEND_INDEX $MEMORY_BYTES_OFFSET $LENGTH_FOUR

# <-----------------------------
# Read the following platform admin registers:
# <-----------------------------

# UUID (8-bytes)
read_admin_register $UUID_OFFSET $LENGTH_EIGHT

# scratch20 (4-bytes)
read_admin_register $SCRATCH_20 $LENGTH_FOUR

# scratch24 (4-bytes)
read_admin_register $SCRATCH_24 $LENGTH_FOUR

# <-----------------------------
# Write to the following admin registers, and read back to verify proper access:
# <-----------------------------

# scratch20 (4-bytes)
write_admin_register $SCRATCH_20 $LENGTH_FOUR 0xa55a4321
read_admin_register $SCRATCH_20 $LENGTH_FOUR
write_admin_register $SCRATCH_20 $LENGTH_FOUR 0x0
read_admin_register $SCRATCH_20 $LENGTH_FOUR

# scratch20 (2-bytes)
write_admin_register $SCRATCH_20 $LENGTH_TWO 0xa55a
read_admin_register $SCRATCH_20 $LENGTH_TWO
write_admin_register $SCRATCH_20 $LENGTH_TWO 0x0
read_admin_register $SCRATCH_20 $LENGTH_TWO

# scratch20 (1-byte)
write_admin_register $SCRATCH_20 $LENGTH_ONE 0xa5
read_admin_register $SCRATCH_20 $LENGTH_ONE
write_admin_register $SCRATCH_20 $LENGTH_ONE 0x0
read_admin_register $SCRATCH_20 $LENGTH_ONE

# scratch24 (4-bytes)
write_admin_register $SCRATCH_24 $LENGTH_FOUR 0xa55a4321
read_admin_register $SCRATCH_24 $LENGTH_FOUR
write_admin_register $SCRATCH_24 $LENGTH_FOUR 0x0
read_admin_register $SCRATCH_24 $LENGTH_FOUR

# scratch24 (2-bytes)
write_admin_register $SCRATCH_24 $LENGTH_TWO 0xa55a
read_admin_register $SCRATCH_24 $LENGTH_TWO
write_admin_register $SCRATCH_24 $LENGTH_TWO 0x0
read_admin_register $SCRATCH_24 $LENGTH_TWO

# scratch24 (1-byte)
write_admin_register $SCRATCH_24 $LENGTH_ONE 0xa5
read_admin_register $SCRATCH_24 $LENGTH_ONE
write_admin_register $SCRATCH_24 $LENGTH_ONE 0x0
read_admin_register $SCRATCH_24 $LENGTH_ONE

# scratch20 (8-bytes)
write_admin_register $SCRATCH_20 $LENGTH_EIGHT 0xa55a432112345aa5
read_admin_register $SCRATCH_20 $LENGTH_EIGHT
write_admin_register $SCRATCH_20 $LENGTH_EIGHT 0x0
read_admin_register $SCRATCH_20 $LENGTH_EIGHT
