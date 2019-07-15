# Original Apple /// Wire List

*[Apple /// Service Reference Manual](ftp://ftp.apple.asimov.net/pub/apple_II/documentation/apple3/service_reference_manual/Apple%20III%20Service%20Reference%20Manual-OCR-1982.pdf), Section II or II, Servicing Information, Chapter 15, Wire List* contains information on **Apple ///** board components and their connections.

The original service manual is a copyrighted document. The reproduction of the wire list is published here under the assumption that the document is an abandonware, which has been made publically available at [archive.org](https://archive.org/details/Apple_III_Service_Reference_Manual-OCR-1982), and with a good will to help the retro computing community with fixing their **Apple ///** machines. Also, an attempt was made to contact Apple wrt copyright and license, but no response has been received.

## Content

  * [`a3-wire-list.txt`](./a3-wire-list.txt) - a digitized version of the original **Wire List** from the service manual.
  * [`a3-parse-wire-list.py`](./a3-parse-wire-list.py) - a script to parse the **Wire List** into board **JSON** file.
  * [`a3-component-locations.csv`](./a3-component-locations.csv) - file describing the location of components on the **Apple ///** board.

### a3-parse-wire-list.py

A script to parse and validate the **Wire List** file and to generate the board **JSON** with all components and traces information. The resulting **JSON** is sent to the standard output.

**SYNTAX:**

```
./a3-parse-wire-list.py <wire-list-file>
```

Where:

```
wire-list-file - an original file with Apple /// wire list
```