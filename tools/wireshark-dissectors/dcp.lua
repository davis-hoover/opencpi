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

dcp_protocol = Proto("DCP",  "OpenCPI DCP Protocol")

pli = ProtoField.uint16("dcp.pli", "payloadLengthIndication", base.DEC)
dmh01 = ProtoField.uint16("dcp.dmh01", "messageHeader01", base.DEC)
dmh2 = ProtoField.uint8("dcp.dmh2", "messageHeader2", base.DEC)
tag = ProtoField.uint8("dcp.tag", "tag", base.DEC)
op = ProtoField.uint8("dcp.op", "operation", base.DEC)
addr = ProtoField.uint32("dcp.addr", "address", base.HEX)
value = ProtoField.uint32("dcp.value", "value", base.HEX_DEC)
worker = ProtoField.uint8("dcp.worker", "worker", base.DEC)
workeraddrspace = ProtoField.uint8("dcp.workeraddrspace", "addrSpace", base.DEC)
workeraddr = ProtoField.uint8("dcp.workeraddr", "workerAddress", base.HEX)

dcp_protocol.fields = { pli, dmh01, dmh2, tag, op, addr, value, worker, workeraddrspace, workeraddr }

function get_message_type(dmh2)
    return bit.band(bit.rshift(dmh2, 4), 0x3)
end

function decode_dmh2(value)
    local flags = ''
    if bit.band(value, 0x80) ~= 0 then flags = flags .. 'Extra ' end
    if bit.band(value, 0x40) ~= 0 then flags = flags .. 'Discovery ' end

    local message_type = get_message_type(value)
    local be = bit.band(value, 0xf)

    if message_type < 3 then
        local message_type_s = ''

        if message_type == 0 then
            message_type_s = 'NOP'
        elseif message_type == 1 then
            message_type_s = 'Write'
        else
            message_type_s = 'Read'
        end

        return message_type_s .. '; Flags: ' .. flags .. 'Byte enable: ' .. be
    else
        resp = ''
        if be == 0 then
            resp = 'OK'
        elseif be == 1 then
             resp = 'Timeout'
        elseif be == 2 then
             resp = 'Error'
        else
             resp = 'Unknown'
        end
        return 'Response ('..resp..'); Flags: ' .. flags
    end
end

function decode_status(reg)
    if reg == 0x0 then
        return "initialize"
    elseif reg == 0x4 then
    return "start"
    elseif reg == 0x8 then
    return "stop"
    elseif reg == 0xc then
    return "release"
    elseif reg == 0x10 then
    return "test"
    elseif reg == 0x14 then
    return "beforeQuery"
    elseif reg == 0x18 then
    return "afterConfigure"
    elseif reg == 0x1c then
    elseif reg == 0x20 then
    return "status"
    elseif reg == 0x24 then
    return "reset"
    end
    return ""
end

function decode_address(addr)
    if addr < 0x1000 then
        return string.format('Admin.0x%x', addr)
    elseif addr < 0x4000 then
        return string.format('?.0x%x', addr)
    elseif addr < 0x40000 then
        local worker = bit.band(bit.rshift(addr, 14), 0x3f) - 1
        local reg = bit.band(addr, 0x3fff)
        return string.format('Control[%d].0x%x '.. decode_status(reg), worker, reg, desc)
    else
        local worker = bit.band(bit.rshift(addr, 20), 0x3f) - 1
        local reg = bit.band(addr, 0xfffff)
        return string.format('Config[%d].0x%x', worker, reg)
    end
end

function decode_address_fields(addr, subtree)
    if addr < 0x1000 then
        subtree:add(workeraddrspace, 0):append_text(' (Admin)')
    elseif addr < 0x4000 then
        -- Invalid
    elseif addr < 0x40000 then
        local workerid = bit.band(bit.rshift(addr, 14), 0x3f) - 1
        local reg = bit.band(addr, 0x3fff)
        subtree:add(workeraddrspace, 1):append_text(' (Control)')
        subtree:add(worker, workerid)
        subtree:add(workeraddr, reg)
    else
        local workerid = bit.band(bit.rshift(addr, 20), 0x3f) - 1
        local reg = bit.band(addr, 0xfffff)
        subtree:add(workeraddrspace, 2):append_text(' (Config)')
        subtree:add(worker, workerid)
        subtree:add(workeraddr, reg)
    end
end

function dcp_protocol.dissector(buffer, pinfo, tree)
    length = buffer:len()
    if length == 0 then return end

    pinfo.cols.protocol = dcp_protocol.name

    local subtree = tree:add(dcp_protocol, buffer(), "OpenCPI DWORD Control Packet")
    subtree:add(pli, buffer(0, 2))
    subtree:add(dmh01, buffer(2, 2))
    local dmh2_string = decode_dmh2(buffer(4, 1):uint())
    subtree:add(dmh2, buffer(4, 1)):append_text(' (' .. dmh2_string .. ')')
    subtree:add(tag, buffer(5, 1))

    local ty = get_message_type(buffer(4, 1):uint())
    if ty == 1 then -- Write
        subtree:add(op, 1):append_text(' (Write)')
        subtree:add(addr, buffer(6, 4))
        decode_address_fields(buffer(6, 4):uint(), subtree)
        subtree:add(value, buffer(10, 4))
        pinfo.cols['info'] = "Write " .. decode_address(buffer(6, 4):uint()) .. ' value ' .. string.format('0x%x', buffer(10, 4):uint())
    elseif ty == 2 then -- Read
        subtree:add(op, 2):append_text(' (Read)')
        subtree:add(addr, buffer(6, 4))
        decode_address_fields(buffer(6, 4):uint(), subtree)
        pinfo.cols['info'] = "Read " .. decode_address(buffer(6, 4):uint())
    elseif ty == 3 then -- Response
        subtree:add(op, 3):append_text(' (Response)')
        subtree:add(value, buffer(6, 4))
        pinfo.cols['info'] = "Response value " .. string.format('0x%x', buffer(6, 4):uint())
    else
        subtree:add(op, 0):append_text(' (NOP)')
    end
end

local ethertype = DissectorTable.get("ethertype")
ethertype:add(0xf040, dcp_protocol)
