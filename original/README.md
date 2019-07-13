# Apple /// Board Schematic Tools

## Original Apple /// Wire List

*[Apple /// Service Reference Manual](ftp://ftp.apple.asimov.net/pub/apple_II/documentation/apple3/service_reference_manual/Apple%20III%20Service%20Reference%20Manual-OCR-1982.pdf), Section II or II, Servicing Information, Chapter 15, Wire List* contains information on **Apple ///** board components and their connections.

A digitized version of the original **Wire List** is in file:
[a3-wire-list.txt](./a3-wire-list.txt)

The original service manual is a copyrighted document. The reproduction of the wire list is published here under the assumption that the document is an abandonware, which has been made publically available at [archive.org](https://archive.org/details/Apple_III_Service_Reference_Manual-OCR-1982), and with a good will to help the retro computing community with fixing their **Apple ///** machines. Also, an attempt was made to contact Apple wrt copyright and license, but no response has been received.

## Wire List Parse Tool

A script [a3-parse-wire-list.py](./a3-parse-wire-list.py) can be used to parse and validate the **Wire List** file and to generate a more useful **JSON** with all components and traces information. From there, there are endless possibilities on writing post processing tools and servicing for the **Apple ///** board.

## JSON Syntax

**JSON** syntax used for the description of the **Apple ///** board is the following:

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
            "part" : "PART-DESCRIPTION",
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
PART-DESCRIPTION - Part description (e.g. 4.7K or S374 or 220U)
PIN-COUNT        - Number of pins in the component
TRACE-ID         - ID (name) of the trace on board that pin is part of (e.g. SUMSND or A11)
                   Traces with no names in the Wire List are automatically named as T001, T002, ...
PART-TYPE        - Type of the component (e.g. SIP8 or MOLEX)
PIN-INDEX        - Index of a pin in a component, starting with 0. Index 0 designated pin number 1.
POSITION-X       - Horizontal position of component's footprint on the A3 board image
POSITION-Y       - Vertical position of component's footprint on the A3 board image
WIDTH            - Width of a component's footprint on the A3 board image (can be negative)
HEIGHT           - Height of a component's footprint on the A3 board image (can be negative)
```

The A3 board image is a photograpic image of the board with dimensions of 3200x2000 pixels and the (0,0) pixel located in bottom left corner of the picture.