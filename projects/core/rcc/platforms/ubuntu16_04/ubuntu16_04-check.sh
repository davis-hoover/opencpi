#!/bin/bash --noprofile
# This file is protected by Copyright. Please refer to the COPYRIGHT file
# distributed with this source distribution.
#
# This file is part of OpenCPI <http://www.opencpi.org>
#
# OpenCPI is free software: you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# OpenCPI is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/>.

[ -r /etc/lsb-release ] && exec 3</etc/lsb-release || exit 1
d_id=''
d_rel=''

IFS='='
while read var val <&3
do
	case $var in
	"DISTRIB_ID")
		d_id=$val
		;;
	"DISTRIB_RELEASE")
		d_rel=$val
		;;
	esac
done
[ $d_id = "Ubuntu" -a $d_rel = "16.04" ]
