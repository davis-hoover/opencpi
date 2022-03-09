.. DRC AD9361 Documentation:

.. This file is protected by Copyright. Please refer to the COPYRIGHT file
   distributed with this source distribution.

   This file is part of OpenCPI <http://www.opencpi.org>

   OpenCPI is free software: you can redistribute it and/or modify it under the
   terms of the GNU Lesser General Public License as published by the Free
   Software Foundation, either version 3 of the License, or (at your option) any
   later version.

   OpenCPI is distributed in the hope that it will be useful, but WITHOUT ANY
   WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
   A PARTICULAR PURPOSE. See the GNU Lesser General Public License for
   more details.

   You should have received a copy of the GNU Lesser General Public License
   along with this program. If not, see <http://www.gnu.org/licenses/>.

.. Company:     Geon Technologies, LLC
   Author:      Davis Hoover and Joel Palmer
   Copyright:   (c) 2018 Geon Technologies, LLC. All rights reserved.
                Dissemination of this information or reproduction of this
                material is strictly prohibited unless prior written
                permission is obtained from Geon Technologies, LLC

.. _DRC_AD9361_Documentation:

cic_dec Constraint Mapping
==========================


+--------------------------------------+--------+-------------------------+---------------------+------------------------+
| DRC API call                         | Data   | Constraint Satisfaction | Underlying API call | Constrained            |
|                                      | Stream | Problem Variable        |                     | Range(s)               |
|                                      | ID     |                         |                     |                        |
+--------------------------------------+--------+-------------------------+---------------------+------------------------+
| N/A                                  | N/A    | r                       | N/A                 | [4..8192]              |
| N/A                                  | N/A    | cic_dec_fc_meghz_in     | N/A                 |                        |
| N/A                                  | N/A    | cic_dec_fc_meghz_out    | N/A                 | cic_dec_fc_meghz_in    |
| N/A                                  | N/A    | cic_dec_bw_meghz_in     | N/A                 |                        |
| N/A                                  | N/A    | cic_dec_bw_meghz_out    | N/A                 | cic_dec_bw_meghz_in/r  |
| N/A                                  | N/A    | cic_dec_fs_megsps_in    | N/A                 |                        |
| N/A                                  | N/A    | cic_dec_fs_megsps_out   | N/A                 | cic_dec_fs_megsps_in/r |
+--------------------------------------+--------+-------------------------+---------------------+------------------------+
