# Keycad

Generates KiCad PCBs for custom keyboards using [Keyboard Layout
Editor](http://www.keyboard-layout-editor.com/) JSON files.

## Current Status

Keycad generates reasonably good PCBs for most conventional layouts, but they
don't have automatic placement of the microcontroller board or of the USB-C
port on the edge, so you'll have to open up the PCB in KiCad and drag them
around yourself.

The generated documentation and QMK snippets for the PCB is correct.

## Installation

* `sudo apt install kicad`  (or however you install KiCad on your system)
* Clone this repo to your machine, and `cd` to that directory.
* `pip3 setup.py install`

Then in KiCad under Preferences -> Manage Symbol Libraries, add the keycad.lib
file as a global library, and then in Preferences -> Manage Symbol Libraries add
the keycad.pretty/ directory as a global footprint library.

## Usage

1. Use [Keyboard Layout Editor](http://www.keyboard-layout-editor.com/) to
   create a keyboard layout for the keyboard you want to build.
2. Download the layout's JSON file. We'll assume it's called `my-keyboard.json`.
3. In the directory containing your file, execute `keycad my-keyboard.json`
4. After a couple moments, KiCad should pop up with a PCB that implements your
   keyboard. Inspect it and make sure the parts are in the right place.
5. Route the board. One way to do this is with Freerouting, a copy of which is included in this project. First export the .dsn of your PCB in KiCad. Then from the root of this project, `java -jar jar/freerouting-executable.jar -de output/my-keyboard.dsn -s`. This project doesn't document how to use Freerouting. When routing is complete, import the .ses file back into KiCad.
6. Pour the fills using `./pour_fills.py [path to your kicad_pcb]`.
7. Go have your PCB manufactured somewhere like [JLCPCB](https://jlcpcb.com/).
8. Order the parts you need from the generated BOM. 
9. When your PCB and parts arrive and you've assembled everything,
   use the code snippets in `my-keyboard-user-guide.md` to customize
   [QMK](https://github.com/qmk/qmk_firmware/) for your keyboard.

## Useful Tools, Prior Art, and Guides

* http://builder.swillkb.com/
* http://www.keyboard-layout-editor.com/
* https://config.qmk.fm/
* https://docs.qmk.fm/
* https://github.com/fcoury/kbpcb
* https://github.com/ruiqimao/keyboard-pcb-guide
* https://kbplate.ai03.me/
* https://keebfol.io/tools
* https://qmk.fm/converter/
* https://wiki.ai03.me/books/pcb-design

## KiCad components and footprints that were copied into here

* `https://github.com/tmk/kicad_lib_tmk`
* `https://github.com/keebio/keebio-components`
* `https://github.com/keebio/Keebio-Parts.pretty`
* `https://github.com/daprice/keyswitches.pretty`
* `https://github.com/tmk/keyboard_parts.pretty`
