#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2001  Donald N. Allingham
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

"""
Provide a rough estimate of the width of a text string.
"""

SWISS = [
0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,
0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,
0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,
0.000,	0.000,	0.278,	0.278,	0.355,	0.556,	0.556,	0.889,	0.667,	0.191,
0.333,	0.333,	0.389,	0.584,	0.278,	0.333,	0.278,	0.278,	0.556,	0.556,
0.556,	0.556,	0.556,	0.556,	0.556,	0.556,	0.556,	0.556,	0.278,	0.278,
0.584,	0.584,	0.584,	0.556,	1.015,	0.667,	0.667,	0.722,	0.722,	0.667,
0.611,	0.778,	0.722,	0.278,	0.500,	0.667,	0.556,	0.833,	0.722,	0.778,
0.667,	0.778,	0.722,	0.667,	0.611,	0.722,	0.667,	0.944,	0.667,	0.667,
0.611,	0.278,	0.278,	0.278,	0.469,	0.556,	0.333,	0.556,	0.556,	0.500,
0.556,	0.556,	0.278,	0.556,	0.556,	0.222,	0.222,	0.500,	0.222,	0.833,
0.556,	0.556,	0.556,	0.556,	0.333,	0.500,	0.278,	0.556,	0.500,	0.722,
0.500,	0.500,	0.500,	0.334,	0.260,	0.334,	0.584,	0.350,	0.556,	0.350,
0.222,	0.556,	0.333,	1.000,	0.556,	0.556,	0.333,	1.000,	0.667,	0.333,
1.000,	0.350,	0.611,	0.350,	0.350,	0.222,	0.222,	0.333,	0.333,	0.350,
0.556,	1.000,	0.333,	1.000,	0.500,	0.333,	0.944,	0.350,	0.500,	0.667,
0.278,	0.333,	0.556,	0.556,	0.556,	0.556,	0.260,	0.556,	0.333,	0.737,
0.370,	0.556,	0.584,	0.333,	0.737,	0.333,	0.400,	0.584,	0.333,	0.333,
0.333,	0.556,	0.537,	0.278,	0.333,	0.333,	0.365,	0.556,	0.834,	0.834,
0.834,	0.611,	0.667,	0.667,	0.667,	0.667,	0.667,	0.667,	1.000,	0.722,
0.667,	0.667,	0.667,	0.667,	0.278,	0.278,	0.278,	0.278,	0.722,	0.722,
0.778,	0.778,	0.778,	0.778,	0.778,	0.584,	0.778,	0.722,	0.722,	0.722,
0.722,	0.667,	0.667,	0.611,	0.556,	0.556,	0.556,	0.556,	0.556,	0.556,
0.889,	0.500,	0.556,	0.556,	0.556,	0.556,	0.278,	0.278,	0.278,	0.278,
0.556,	0.556,	0.556,	0.556,	0.556,	0.556,	0.556,	0.584,	0.611,	0.556,
0.556,	0.556,	0.556,	0.500,	0.556,	0.500]

SWISS_B = [
0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,
0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,
0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,
0.000,	0.000,	0.278,	0.333,	0.474,	0.556,	0.556,	0.889,	0.722,	0.238,
0.333,	0.333,	0.389,	0.584,	0.278,	0.333,	0.278,	0.278,	0.556,	0.556,
0.556,	0.556,	0.556,	0.556,	0.556,	0.556,	0.556,	0.556,	0.333,	0.333,
0.584,	0.584,	0.584,	0.611,	0.975,	0.722,	0.722,	0.722,	0.722,	0.667,
0.611,	0.778,	0.722,	0.278,	0.556,	0.722,	0.611,	0.833,	0.722,	0.778,
0.667,	0.778,	0.722,	0.667,	0.611,	0.722,	0.667,	0.944,	0.667,	0.667,
0.611,	0.333,	0.278,	0.333,	0.584,	0.556,	0.333,	0.556,	0.611,	0.556,
0.611,	0.556,	0.333,	0.611,	0.611,	0.278,	0.278,	0.556,	0.278,	0.889,
0.611,	0.611,	0.611,	0.611,	0.389,	0.556,	0.333,	0.611,	0.556,	0.778,
0.556,	0.556,	0.500,	0.389,	0.280,	0.389,	0.584,	0.350,	0.556,	0.350,
0.278,	0.556,	0.500,	1.000,	0.556,	0.556,	0.333,	1.000,	0.667,	0.333,
1.000,	0.350,	0.611,	0.350,	0.350,	0.278,	0.278,	0.500,	0.500,	0.350,
0.556,	1.000,	0.333,	1.000,	0.556,	0.333,	0.944,	0.350,	0.500,	0.667,
0.278,	0.333,	0.556,	0.556,	0.556,	0.556,	0.280,	0.556,	0.333,	0.737,
0.370,	0.556,	0.584,	0.333,	0.737,	0.333,	0.400,	0.584,	0.333,	0.333,
0.333,	0.611,	0.556,	0.278,	0.333,	0.333,	0.365,	0.556,	0.834,	0.834,
0.834,	0.611,	0.722,	0.722,	0.722,	0.722,	0.722,	0.722,	1.000,	0.722,
0.667,	0.667,	0.667,	0.667,	0.278,	0.278,	0.278,	0.278,	0.722,	0.722,
0.778,	0.778,	0.778,	0.778,	0.778,	0.584,	0.778,	0.722,	0.722,	0.722,
0.722,	0.667,	0.667,	0.611,	0.556,	0.556,	0.556,	0.556,	0.556,	0.556,
0.889,	0.556,	0.556,	0.556,	0.556,	0.556,	0.278,	0.278,	0.278,	0.278,
0.611,	0.611,	0.611,	0.611,	0.611,	0.611,	0.611,	0.584,	0.611,	0.611,
0.611,	0.611,	0.611,	0.556,	0.611,	0.556]

SWISS_I = [
0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,
0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,
0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,
0.000,	0.000,	0.278,	0.278,	0.355,	0.556,	0.556,	0.889,	0.667,	0.191,
0.333,	0.333,	0.389,	0.584,	0.278,	0.333,	0.278,	0.278,	0.556,	0.556,
0.556,	0.556,	0.556,	0.556,	0.556,	0.556,	0.556,	0.556,	0.278,	0.278,
0.584,	0.584,	0.584,	0.556,	1.015,	0.667,	0.667,	0.722,	0.722,	0.667,
0.611,	0.778,	0.722,	0.278,	0.500,	0.667,	0.556,	0.833,	0.722,	0.778,
0.667,	0.778,	0.722,	0.667,	0.611,	0.722,	0.667,	0.944,	0.667,	0.667,
0.611,	0.278,	0.278,	0.278,	0.469,	0.556,	0.333,	0.556,	0.556,	0.500,
0.556,	0.556,	0.278,	0.556,	0.556,	0.222,	0.222,	0.500,	0.222,	0.833,
0.556,	0.556,	0.556,	0.556,	0.333,	0.500,	0.278,	0.556,	0.500,	0.722,
0.500,	0.500,	0.500,	0.334,	0.260,	0.334,	0.584,	0.350,	0.556,	0.350,
0.222,	0.556,	0.333,	1.000,	0.556,	0.556,	0.333,	1.000,	0.667,	0.333,
1.000,	0.350,	0.611,	0.350,	0.350,	0.222,	0.222,	0.333,	0.333,	0.350,
0.556,	1.000,	0.333,	1.000,	0.500,	0.333,	0.944,	0.350,	0.500,	0.667,
0.278,	0.333,	0.556,	0.556,	0.556,	0.556,	0.260,	0.556,	0.333,	0.737,
0.370,	0.556,	0.584,	0.333,	0.737,	0.333,	0.400,	0.584,	0.333,	0.333,
0.333,	0.556,	0.537,	0.278,	0.333,	0.333,	0.365,	0.556,	0.834,	0.834,
0.834,	0.611,	0.667,	0.667,	0.667,	0.667,	0.667,	0.667,	1.000,	0.722,
0.667,	0.667,	0.667,	0.667,	0.278,	0.278,	0.278,	0.278,	0.722,	0.722,
0.778,	0.778,	0.778,	0.778,	0.778,	0.584,	0.778,	0.722,	0.722,	0.722,
0.722,	0.667,	0.667,	0.611,	0.556,	0.556,	0.556,	0.556,	0.556,	0.556,
0.889,	0.500,	0.556,	0.556,	0.556,	0.556,	0.278,	0.278,	0.278,	0.278,
0.556,	0.556,	0.556,	0.556,	0.556,	0.556,	0.556,	0.584,	0.611,	0.556,
0.556,	0.556,	0.556,	0.500,	0.556,	0.500]

SWISS_BI = [
0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,
0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,
0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,
0.000,	0.000,	0.278,	0.333,	0.474,	0.556,	0.556,	0.889,	0.722,	0.238,
0.333,	0.333,	0.389,	0.584,	0.278,	0.333,	0.278,	0.278,	0.556,	0.556,
0.556,	0.556,	0.556,	0.556,	0.556,	0.556,	0.556,	0.556,	0.333,	0.333,
0.584,	0.584,	0.584,	0.611,	0.975,	0.722,	0.722,	0.722,	0.722,	0.667,
0.611,	0.778,	0.722,	0.278,	0.556,	0.722,	0.611,	0.833,	0.722,	0.778,
0.667,	0.778,	0.722,	0.667,	0.611,	0.722,	0.667,	0.944,	0.667,	0.667,
0.611,	0.333,	0.278,	0.333,	0.584,	0.556,	0.333,	0.556,	0.611,	0.556,
0.611,	0.556,	0.333,	0.611,	0.611,	0.278,	0.278,	0.556,	0.278,	0.889,
0.611,	0.611,	0.611,	0.611,	0.389,	0.556,	0.333,	0.611,	0.556,	0.778,
0.556,	0.556,	0.500,	0.389,	0.280,	0.389,	0.584,	0.350,	0.556,	0.350,
0.278,	0.556,	0.500,	1.000,	0.556,	0.556,	0.333,	1.000,	0.667,	0.333,
1.000,	0.350,	0.611,	0.350,	0.350,	0.278,	0.278,	0.500,	0.500,	0.350,
0.556,	1.000,	0.333,	1.000,	0.556,	0.333,	0.944,	0.350,	0.500,	0.667,
0.278,	0.333,	0.556,	0.556,	0.556,	0.556,	0.280,	0.556,	0.333,	0.737,
0.370,	0.556,	0.584,	0.333,	0.737,	0.333,	0.400,	0.584,	0.333,	0.333,
0.333,	0.611,	0.556,	0.278,	0.333,	0.333,	0.365,	0.556,	0.834,	0.834,
0.834,	0.611,	0.722,	0.722,	0.722,	0.722,	0.722,	0.722,	1.000,	0.722,
0.667,	0.667,	0.667,	0.667,	0.278,	0.278,	0.278,	0.278,	0.722,	0.722,
0.778,	0.778,	0.778,	0.778,	0.778,	0.584,	0.778,	0.722,	0.722,	0.722,
0.722,	0.667,	0.667,	0.611,	0.556,	0.556,	0.556,	0.556,	0.556,	0.556,
0.889,	0.556,	0.556,	0.556,	0.556,	0.556,	0.278,	0.278,	0.278,	0.278,
0.611,	0.611,	0.611,	0.611,	0.611,	0.611,	0.611,	0.584,	0.611,	0.611,
0.611,	0.611,	0.611,	0.556,	0.611,	0.556]

ROMAN = [
0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,
0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,
0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,
0.000,	0.000,	0.250,	0.333,	0.408,	0.500,	0.500,	0.833,	0.778,	0.180,
0.333,	0.333,	0.500,	0.564,	0.250,	0.333,	0.250,	0.278,	0.500,	0.500,
0.500,	0.500,	0.500,	0.500,	0.500,	0.500,	0.500,	0.500,	0.278,	0.278,
0.564,	0.564,	0.564,	0.444,	0.921,	0.722,	0.667,	0.667,	0.722,	0.611,
0.556,	0.722,	0.722,	0.333,	0.389,	0.722,	0.611,	0.889,	0.722,	0.722,
0.556,	0.722,	0.667,	0.556,	0.611,	0.722,	0.722,	0.944,	0.722,	0.722,
0.611,	0.333,	0.278,	0.333,	0.469,	0.500,	0.333,	0.444,	0.500,	0.444,
0.500,	0.444,	0.333,	0.500,	0.500,	0.278,	0.278,	0.500,	0.278,	0.778,
0.500,	0.500,	0.500,	0.500,	0.333,	0.389,	0.278,	0.500,	0.500,	0.722,
0.500,	0.500,	0.444,	0.480,	0.200,	0.480,	0.541,	0.350,	0.500,	0.350,
0.333,	0.500,	0.444,	1.000,	0.500,	0.500,	0.333,	1.000,	0.556,	0.333,
0.889,	0.350,	0.611,	0.350,	0.350,	0.333,	0.333,	0.444,	0.444,	0.350,
0.500,	1.000,	0.333,	0.980,	0.389,	0.333,	0.722,	0.350,	0.444,	0.722,
0.250,	0.333,	0.500,	0.500,	0.500,	0.500,	0.200,	0.500,	0.333,	0.760,
0.276,	0.500,	0.564,	0.333,	0.760,	0.333,	0.400,	0.564,	0.300,	0.300,
0.333,	0.500,	0.453,	0.250,	0.333,	0.300,	0.310,	0.500,	0.750,	0.750,
0.750,	0.444,	0.722,	0.722,	0.722,	0.722,	0.722,	0.722,	0.889,	0.667,
0.611,	0.611,	0.611,	0.611,	0.333,	0.333,	0.333,	0.333,	0.722,	0.722,
0.722,	0.722,	0.722,	0.722,	0.722,	0.564,	0.722,	0.722,	0.722,	0.722,
0.722,	0.722,	0.556,	0.500,	0.444,	0.444,	0.444,	0.444,	0.444,	0.444,
0.667,	0.444,	0.444,	0.444,	0.444,	0.444,	0.278,	0.278,	0.278,	0.278,
0.500,	0.500,	0.500,	0.500,	0.500,	0.500,	0.500,	0.564,	0.500,	0.500,
0.500,	0.500,	0.500,	0.500,	0.500,	0.500]

ROMAN_B = [
0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,
0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,
0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,
0.000,	0.000,	0.250,	0.333,	0.555,	0.500,	0.500,	1.000,	0.833,	0.278,
0.333,	0.333,	0.500,	0.570,	0.250,	0.333,	0.250,	0.278,	0.500,	0.500,
0.500,	0.500,	0.500,	0.500,	0.500,	0.500,	0.500,	0.500,	0.333,	0.333,
0.570,	0.570,	0.570,	0.500,	0.930,	0.722,	0.667,	0.722,	0.722,	0.667,
0.611,	0.778,	0.778,	0.389,	0.500,	0.778,	0.667,	0.944,	0.722,	0.778,
0.611,	0.778,	0.722,	0.556,	0.667,	0.722,	0.722,	1.000,	0.722,	0.722,
0.667,	0.333,	0.278,	0.333,	0.581,	0.500,	0.333,	0.500,	0.556,	0.444,
0.556,	0.444,	0.333,	0.500,	0.556,	0.278,	0.333,	0.556,	0.278,	0.833,
0.556,	0.500,	0.556,	0.556,	0.444,	0.389,	0.333,	0.556,	0.500,	0.722,
0.500,	0.500,	0.444,	0.394,	0.220,	0.394,	0.520,	0.350,	0.500,	0.350,
0.333,	0.500,	0.500,	1.000,	0.500,	0.500,	0.333,	1.000,	0.556,	0.333,
1.000,	0.350,	0.667,	0.350,	0.350,	0.333,	0.333,	0.500,	0.500,	0.350,
0.500,	1.000,	0.333,	1.000,	0.389,	0.333,	0.722,	0.350,	0.444,	0.722,
0.250,	0.333,	0.500,	0.500,	0.500,	0.500,	0.220,	0.500,	0.333,	0.747,
0.300,	0.500,	0.570,	0.333,	0.747,	0.333,	0.400,	0.570,	0.300,	0.300,
0.333,	0.556,	0.540,	0.250,	0.333,	0.300,	0.330,	0.500,	0.750,	0.750,
0.750,	0.500,	0.722,	0.722,	0.722,	0.722,	0.722,	0.722,	1.000,	0.722,
0.667,	0.667,	0.667,	0.667,	0.389,	0.389,	0.389,	0.389,	0.722,	0.722,
0.778,	0.778,	0.778,	0.778,	0.778,	0.570,	0.778,	0.722,	0.722,	0.722,
0.722,	0.722,	0.611,	0.556,	0.500,	0.500,	0.500,	0.500,	0.500,	0.500,
0.722,	0.444,	0.444,	0.444,	0.444,	0.444,	0.278,	0.278,	0.278,	0.278,
0.500,	0.556,	0.500,	0.500,	0.500,	0.500,	0.500,	0.570,	0.500,	0.556,
0.556,	0.556,	0.556,	0.500,	0.556,	0.500]

ROMAN_I = [
0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,
0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,
0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,
0.000,	0.000,	0.250,	0.333,	0.420,	0.500,	0.500,	0.833,	0.778,	0.214,
0.333,	0.333,	0.500,	0.675,	0.250,	0.333,	0.250,	0.278,	0.500,	0.500,
0.500,	0.500,	0.500,	0.500,	0.500,	0.500,	0.500,	0.500,	0.333,	0.333,
0.675,	0.675,	0.675,	0.500,	0.920,	0.611,	0.611,	0.667,	0.722,	0.611,
0.611,	0.722,	0.722,	0.333,	0.444,	0.667,	0.556,	0.833,	0.667,	0.722,
0.611,	0.722,	0.611,	0.500,	0.556,	0.722,	0.611,	0.833,	0.611,	0.556,
0.556,	0.389,	0.278,	0.389,	0.422,	0.500,	0.333,	0.500,	0.500,	0.444,
0.500,	0.444,	0.278,	0.500,	0.500,	0.278,	0.278,	0.444,	0.278,	0.722,
0.500,	0.500,	0.500,	0.500,	0.389,	0.389,	0.278,	0.500,	0.444,	0.667,
0.444,	0.444,	0.389,	0.400,	0.275,	0.400,	0.541,	0.350,	0.500,	0.350,
0.333,	0.500,	0.556,	0.889,	0.500,	0.500,	0.333,	1.000,	0.500,	0.333,
0.944,	0.350,	0.556,	0.350,	0.350,	0.333,	0.333,	0.556,	0.556,	0.350,
0.500,	0.889,	0.333,	0.980,	0.389,	0.333,	0.667,	0.350,	0.389,	0.556,
0.250,	0.389,	0.500,	0.500,	0.500,	0.500,	0.275,	0.500,	0.333,	0.760,
0.276,	0.500,	0.675,	0.333,	0.760,	0.333,	0.400,	0.675,	0.300,	0.300,
0.333,	0.500,	0.523,	0.250,	0.333,	0.300,	0.310,	0.500,	0.750,	0.750,
0.750,	0.500,	0.611,	0.611,	0.611,	0.611,	0.611,	0.611,	0.889,	0.667,
0.611,	0.611,	0.611,	0.611,	0.333,	0.333,	0.333,	0.333,	0.722,	0.667,
0.722,	0.722,	0.722,	0.722,	0.722,	0.675,	0.722,	0.722,	0.722,	0.722,
0.722,	0.556,	0.611,	0.500,	0.500,	0.500,	0.500,	0.500,	0.500,	0.500,
0.667,	0.444,	0.444,	0.444,	0.444,	0.444,	0.278,	0.278,	0.278,	0.278,
0.500,	0.500,	0.500,	0.500,	0.500,	0.500,	0.500,	0.675,	0.500,	0.500,
0.500,	0.500,	0.500,	0.444,	0.500,	0.444]

ROMAN_BI = [
0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,
0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,
0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,	0.000,
0.000,	0.000,	0.250,	0.389,	0.555,	0.500,	0.500,	0.833,	0.778,	0.278,
0.333,	0.333,	0.500,	0.570,	0.250,	0.333,	0.250,	0.278,	0.500,	0.500,
0.500,	0.500,	0.500,	0.500,	0.500,	0.500,	0.500,	0.500,	0.333,	0.333,
0.570,	0.570,	0.570,	0.500,	0.832,	0.667,	0.667,	0.667,	0.722,	0.667,
0.667,	0.722,	0.778,	0.389,	0.500,	0.667,	0.611,	0.889,	0.722,	0.722,
0.611,	0.722,	0.667,	0.556,	0.611,	0.722,	0.667,	0.889,	0.667,	0.611,
0.611,	0.333,	0.278,	0.333,	0.570,	0.500,	0.333,	0.500,	0.500,	0.444,
0.500,	0.444,	0.333,	0.500,	0.556,	0.278,	0.278,	0.500,	0.278,	0.778,
0.556,	0.500,	0.500,	0.500,	0.389,	0.389,	0.278,	0.556,	0.444,	0.667,
0.500,	0.444,	0.389,	0.348,	0.220,	0.348,	0.570,	0.350,	0.500,	0.350,
0.333,	0.500,	0.500,	1.000,	0.500,	0.500,	0.333,	1.000,	0.556,	0.333,
0.944,	0.350,	0.611,	0.350,	0.350,	0.333,	0.333,	0.500,	0.500,	0.350,
0.500,	1.000,	0.333,	1.000,	0.389,	0.333,	0.722,	0.350,	0.389,	0.611,
0.250,	0.389,	0.500,	0.500,	0.500,	0.500,	0.220,	0.500,	0.333,	0.747,
0.266,	0.500,	0.606,	0.333,	0.747,	0.333,	0.400,	0.570,	0.300,	0.300,
0.333,	0.576,	0.500,	0.250,	0.333,	0.300,	0.300,	0.500,	0.750,	0.750,
0.750,	0.500,	0.667,	0.667,	0.667,	0.667,	0.667,	0.667,	0.944,	0.667,
0.667,	0.667,	0.667,	0.667,	0.389,	0.389,	0.389,	0.389,	0.722,	0.722,
0.722,	0.722,	0.722,	0.722,	0.722,	0.570,	0.722,	0.722,	0.722,	0.722,
0.722,	0.611,	0.611,	0.500,	0.500,	0.500,	0.500,	0.500,	0.500,	0.500,
0.722,	0.444,	0.444,	0.444,	0.444,	0.444,	0.278,	0.278,	0.278,	0.278,
0.500,	0.556,	0.500,	0.500,	0.500,	0.500,	0.500,	0.570,	0.500,	0.556,
0.556,	0.556,	0.556,	0.444,	0.500,	0.444]

FONT_ARRAY = [ [SWISS, SWISS_B, SWISS_I, SWISS_BI ],
               [ROMAN, ROMAN_B, ROMAN_I, ROMAN_BI ] ]

#-------------------------------------------------------------------------
#
# string_width
#
#-------------------------------------------------------------------------
def string_width(font, text):
    """
    returns with width of a string in the specified font
    """
    ## TODO: Does it not make sense to use writing on a pango Layout to know
    ##       text width?
    i = font.get_type_face()
    j = font.get_bold() + font.get_italic()*2
    s = font.get_size()
    l = FONT_ARRAY[i][j]
    r = 0
    for c in text:
        try:
            r = r + l[ord(c)]
        except:
            r = r + l[ord('n')]
    return (r+1)*s

def string_trim(font, text, width, ellipses = "..."):
    """
    Like string_width, but this makes sure the length of the
    string is <= width. Optionally, add ellipses (...).
    """
    i = font.get_type_face()
    j = font.get_bold() + font.get_italic()*2
    s = font.get_size()
    l = FONT_ARRAY[i][j]
    ellipses_length = 0
    # get length of each letter
    for c in ellipses:
        try:
            ellipses_length += l[ord(c)]
        except:
            ellipses_length += l[ord('n')]
    # find the part that is < width
    retval = ""
    sumlen = 0
    length = 0
    for i in range(len(text)):
        c = text[i]
        try:
            length = l[ord(c)]
        except:
            length = l[ord('n')]
        # too long:
        if (sumlen + length + 1) * s > width:
            if ellipses_length > 0:
                # try again with ellipses
                retval += c
                sumlen += length
                break
            else:
                # return just this so far
                return retval
        retval += c
        sumlen += length
    # if exited out the bottom:
    if (sumlen + 1) * s <= width:
        return text
    # too long; try again with ellipses
    retval = ""
    sumlen = 0
    length = 0
    for i in range(len(text)):
        c = text[i]
        try:
            length = l[ord(c)]
        except:
            length = l[ord('n')]
        if (sumlen + length + 1) * s > width:
            return retval
        if (sumlen + length + ellipses_length + 1) * s > width:
            return retval + ellipses
        retval += c
        sumlen += length
    # should not exit out the bottom!
    return text
