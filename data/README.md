# Board Data Files

This directory contains **JSON** files describing boards.

### JSON Syntax

```
{
    components : {
        "COMPONENT-ID" : {
            "box" : [
                POSITION-X,
                POSITION-Y,
                WIDTH,
                HEIGHT
            ],
            "id" : "COMPONENT-ID",
            "location" : "BOARD-LOCATION",
            "pages" : [
                SCHEMATIC-PAGE,
                ...
            ],
            "part" : "PART-VALUE",
            "pin_count" : PIN-COUNT,
            "pins" : [
                "TRACE-ID",
                ...
            ],
            "type" : "PART-TYPE"
        },
        ...
    },
    traces : {
        "TRACE-ID" : [
            "COMPONENT-ID",
            PIN-INDEX
        ],
        ...
    }    
}
```

Where:

```
COMPONENT-ID     - Part Reference Designator (e.g. U176 or C12)
BOARD-LOCATION   - Coordinates of location on board A-N/1-14 (e.g. A7 or L12)
SCHEMATIC-PAGE   - Page number on schematic pages from the service manual
PART-VALUE       - Part's value (e.g. 4.7K or S374 or 220U)
PIN-COUNT        - Number of pins in the component
TRACE-ID         - ID (name) of the trace on board that pin is part of (e.g. SUMSND or A11)
                   Traces with no names in the Wire List are automatically named as T001, T002, ...
PART-TYPE        - Type of the component (e.g. SIP8 or MOLEX)
PIN-INDEX        - Index of a pin in a component, starting with 0. Index 0 designated pin number 1.
POSITION-X       - Horizontal position of component's footprint on the A3 board image
POSITION-Y       - Vertical position of component's footprint on the A3 board image
WIDTH            - Width of a component's footprint on the board image (can be negative)
HEIGHT           - Height of a component's footprint on the board image (can be negative)
```

The board image is a photograpic image of the board with dimensions of 3200x2000 pixels and the (0,0) pixel located in bottom left corner of the picture.