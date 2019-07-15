# Original Board Data

This directory contains files with the **original** data and scripts to transform this data into **JSON** form. For the **JSON** syntax, please see the [`data`](../data) directory.

## Content

  * [`apple3`](./apple3) - directory with **Apple ///** data
  * [`add-locations.py`](./add-locations.py) - script to inject component locations on the board into the **JSON** file
  * [`components.txt`](./components.txt) - text file with description of electronic components found on the boards

### add-locations.py

**SYNTAX:**

```
add-locations.py <locations-file.csv> <json-file.json>
```

This script parses a **CSV** file containing coordinates of components on a board and injects them into the existing **JSON** file with board definition. The resulting **JSON** is sent to the standard output.

The **CSV** file should contain components in individual lines with the following syntax:

```
ID,X,Y,W,H
```

Where:

```
ID  - Component's ID, used as a key to the components table in the JSON file
X,Y - Coordinates on the board, with `0,0` point located in the lower left corner of the image. 
      The coordinates should point to the location closest to a pin 1 of the component.
W,H - Width and height of the component. 
      These values can be negative, depending on the orientation of the component.

```

### components.txt

This file contains description of electronic components found on boards. The description is used to determine the inputs and outputs of the component pins and to build a board connection graph.

The file should contain components descriptions separated by empty line(s). A single component description should follow the syntax:

```
<ID>,<DESCRIPTION>
1=<PIN-ID>, <PIN-TYPE> [, (<INPUTS>)]
2=<PIN-ID>, <PIN-TYPE> [, (<INPUTS>)]
...
```

Where:

```
ID          - ID of the component part, e.g. 7400
DESCRIPTION - Description of the part
PIN-ID      - ID of the component's pin
PIN-TYPE    - type of the pin, one of:
              I - pin is an input  
              O - pin is an output  
              B - pin is a bi-directional  
              C - pin is a clock input
              G - pin is a connection to ground
              P - pin is a power input  
INPUTS      - For O and B pin type, the list of I or C pins which act as inputs for the output pin.
              State of these pins will impact the state of the output pin.
              If the output is autonomously generated at the component (e.g. in a CPU), 
              the list should be (-).            
```
