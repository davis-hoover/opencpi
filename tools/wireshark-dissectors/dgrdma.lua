-- This file is protected by Copyright. Please refer to the COPYRIGHT file
-- distributed with this source distribution.
--
-- This file is part of OpenCPI <http://www.opencpi.org>
--
-- OpenCPI is free software: you can redistribute it and/or modify it under the
-- terms of the GNU Lesser General Public License as published by the Free
-- Software Foundation, either version 3 of the License, or (at your option) any
-- later version.
--
-- OpenCPI is distributed in the hope that it will be useful, but WITHOUT ANY
-- WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
-- A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
-- details.
--
-- You should have received a copy of the GNU Lesser General Public License
-- along with this program. If not, see <http://www.gnu.org/licenses/>.

dgrdma_protocol = Proto("DGRDMA",  "OpenCPI DG-RDMA Protocol")

-- frame header
src_id = ProtoField.uint16("dgrdma.src_id", "srcId", base.DEC)
dst_id = ProtoField.uint16("dgrdma.dst_id", "dstId", base.DEC)
frameseq = ProtoField.uint16("dgrdma.frameseq", "frameSequence", base.DEC)
ackstart = ProtoField.uint16("dgrdma.ackstart", "ackStart", base.DEC)
ackcount = ProtoField.uint8("dgrdma.ackcount", "ackCount", base.DEC)
flags = ProtoField.uint8("dgrdma.flags", "flags", base.HEX)

-- message header
transactionid = ProtoField.uint32("dgrdma.transactionid", "transactionId", base.DEC)
flagaddr = ProtoField.uint32("dgrdma.flagaddr", "flagaddr", base.HEX)
flagvalue = ProtoField.uint32("dgrdma.flagvalue", "flagvalue", base.HEX)
msgsintransaction = ProtoField.uint16("dgrdma.msgsintransaction", "msgsintransaction", base.DEC)
msgsequence = ProtoField.uint16("dgrdma.msgsequence", "msgsequence", base.DEC)
dataaddr = ProtoField.uint32("dgrdma.dataaddr", "dataaddr", base.HEX)
datalen = ProtoField.uint16("dgrdma.datalen", "datalen", base.DEC_HEX)
type = ProtoField.uint8("dgrdma.type", "type", base.DEC)
nextmsg = ProtoField.uint8("dgrdma.nextmsg", "nextmsg", base.HEX)
payload = ProtoField.bytes("dgrdma.payload", "payload", base.SPACE)

dgrdma_protocol.fields = {
    src_id, dst_id, frameseq, ackstart, ackcount, flags,
    transactionid, flagaddr, flagvalue, msgsintransaction, msgsequence, dataaddr, datalen, type, nextmsg,
    payload
}

function dgrdma_protocol.dissector(buffer, pinfo, tree)
    length = buffer:len()
    if length == 0 then return end

    pinfo.cols.protocol = dgrdma_protocol.name

    local subtree = tree:add(dgrdma_protocol, buffer(), "OpenCPI Datagram")

    -- Parse frame header
    subtree:add_le(src_id, buffer(0, 2))
    subtree:add_le(dst_id, buffer(2, 2))
    subtree:add_le(frameseq, buffer(4, 2))
    subtree:add_le(ackstart, buffer(6, 2))
    subtree:add_le(ackcount, buffer(8, 1))
    subtree:add_le(flags, buffer(9, 1))

    local more_messages = (buffer(9, 1):uint() ~= 0)

    -- Default if no messages
    local frameseq = buffer(4,2):le_uint()
    local acks = buffer(6,2):le_uint()
    local ackn = buffer(8,1):le_uint()
    if ackn == 0 then
        ack_str = string.format('             ')
    else
        ack_str = string.format('ack %5d/%3d', acks, ackn)
    end

    local info_string = string.format('frameseq %d %s', frameseq, ack_str)

    -- Parse message headers
    local msg_num = 1
    local buffer_ptr = 10
    while more_messages do
        payload_len = buffer(buffer_ptr+20, 2):le_uint()
        txn_id = buffer(buffer_ptr+0, 4):le_uint()
        nmsgs = buffer(buffer_ptr+12, 2):le_uint()
        seq = buffer(buffer_ptr+14, 2):le_uint()

        info_string = info_string .. string.format('; Txn %2d (%d/%d) %4d bytes', txn_id, seq, nmsgs, payload_len)

        -- message header length = 24
        local msg_tree = subtree:add(dgrdma_protocol, buffer(buffer_ptr, 24 + payload_len), string.format("Message %d (%d bytes)", msg_num, payload_len))

        msg_tree:add_le(transactionid, buffer(buffer_ptr+0, 4))
        msg_tree:add_le(flagaddr, buffer(buffer_ptr+4, 4))
        msg_tree:add_le(flagvalue, buffer(buffer_ptr+8, 4)):append_text(decode_flag_value(buffer(buffer_ptr+8, 4):le_uint()))
        msg_tree:add_le(msgsintransaction, buffer(buffer_ptr+12, 2))
        msg_tree:add_le(msgsequence, buffer(buffer_ptr+14, 2))
        msg_tree:add_le(dataaddr, buffer(buffer_ptr+16, 4))
        msg_tree:add_le(datalen, buffer(buffer_ptr+20, 2))
        msg_tree:add_le(type, buffer(buffer_ptr+22, 1))
        msg_tree:add_le(nextmsg, buffer(buffer_ptr+23, 1))
        msg_tree:add(payload, buffer(buffer_ptr+24, payload_len))

        more_messages = (buffer(buffer_ptr+23, 1):uint() ~= 0)

        -- round payload_len up to a multiple of 8 to allow for padding bytes
        payload_len = math.floor((payload_len + 7) / 8) * 8
        buffer_ptr = buffer_ptr + 24 + payload_len
        msg_num = msg_num + 1
    end

    if msg_num == 1 then
        info_string = info_string .. ' (ACK-only)'
    end
    pinfo.cols.info = info_string
end

function decode_flag_value(value)
    if value ~= 0xffffffff then
        length = bit.band(bit.rshift(value, 1), 0x1fffff)
        opcode = bit.band(bit.rshift(value, 24), 0xff)
        result = string.format(' length=%d, opcode=%d', length, opcode)
        if bit.band(bit.rshift(value, 22), 1) == 1 then
            result = result .. ', eof'
        end
        if bit.band(bit.rshift(value, 22), 1) == 1 then
            result = result .. ', trunc'
        end
        return result
    else
        return ''
    end
end

local ethertype = DissectorTable.get("ethertype")
ethertype:add(0xf042, dgrdma_protocol)
