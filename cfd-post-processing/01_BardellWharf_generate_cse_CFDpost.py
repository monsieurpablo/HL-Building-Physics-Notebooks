header = """# Session file started:  2022/06/07 20:58:39
# CFX-21.2

# To avoid unnecessary file pre-processing and modifications, include
# COMMAND FILE at the top of your session file.
# If it is not included, the file is assumed to be older and will be
# modified for backward compatibility.
COMMAND FILE:
  CFX Post Version = 21.2
END

>readstate filename=E:/Bardell/Baseline000_forPablo.cst, mode=append, load=false, \
keepexpressions=true"""


body = """
DATA READER:
  Domains to Load=
END

> load filename={0}, case=Case \
{1}, force_reload=true

EXPORT:
  ANSYS Export Data = Element Heat Flux
  ANSYS Export Locator = /USER SURFACE:ghSurface
  ANSYS File Format = ANSYS
  ANSYS Reference Temperature = 0.0 [K]
  ANSYS Specify Reference Temperature = Off
  ANSYS Supplemental HTC = 0.0 [W m^-2 K^-1]
  Additional Variable List =
  BC Profile Type = Inlet Velocity
  CSV Type = CSV
  Case Name = Case Baseline090_001
  Export Connectivity = Off
  Export Coord Frame = Global
  Export File = E:/Bardell/Export/{1}.csv
  Export Geometry = On
  Export Location Aliases =
  Export Node Numbers = On
  Export Null Data = On
  Export Type = Generic
  Export Units System = Current
  Export Variable Type = Current
  External Export Data = None
  Include File Information = Off
  Include Header = On
  Location = Buildings
  Location List = /USER SURFACE:ghSurface
  Null Token = null
  Overwrite = On
  Precision = 8
  Separator = ", "
  Spatial Variables = Y
  Variable List = Velocity Ratio, Velocity Ratio at 10m, Velocity u, Velocity \
v, Velocity w
  Vector Brackets = ()
  Vector Display = Scalar
END
>export"""

# from glob import glob
# files = glob("*.res")
# print(files)

import os

folder = "E:/Bardell/Baseline/"

files = [f"Baseline{dir:03d}_001.res" for dir in range(0,360, 10)]
# cases = [file.split('.res')[0] for file in files]


with open('pablo_bardell.cse' , 'w') as f:
    f.write(header)
    
    for file in files:
        # get case name from file path
        case = file.split('.res')[0]
        
        print(file)
        print(case)
        
        f.write(body.format(os.path.join(folder,file), case))
    
    
