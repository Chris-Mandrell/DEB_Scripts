# Do an initialization of SharpCap consistently for DEB teams

SharpCap.SelectedCamera = SharpCap.Cameras[0]
SharpCap.SelectedCamera.Controls.Gain.Value = 0
SharpCap.SelectedCamera.Controls.BlackLevel.Value = 100
SharpCap.SelectedCamera.Controls.Resolution.Value = SharpCap.SelectedCamera.Controls.Resolution.AvailableValues[0]
SharpCap.SelectedCamera.LiveView = True
