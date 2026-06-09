"""SharpCap IronPython initialization of SharpCap consistently for DEB teams
Copyright (C) 2024  Dynamic Eclipse Broadcast (DEB) Initiative

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

Author: Chris Mandrell
"""

SharpCap.SelectedCamera = SharpCap.Cameras[0]
SharpCap.SelectedCamera.Controls.Gain.Value = 0
SharpCap.SelectedCamera.Controls.BlackLevel.Value = 100
SharpCap.SelectedCamera.Controls.Resolution.Value = SharpCap.SelectedCamera.Controls.Resolution.AvailableValues[0]
SharpCap.SelectedCamera.LiveView = True
