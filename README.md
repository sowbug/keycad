# keycad

Generates KiCad PCBs for custom keyboards.

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
5. Go have your PCB manufactured somewhere like [JLCPCB](https://jlcpcb.com/).
6. TODO: Order the parts you need from the generated BOM. 
7. TODO: when your PCB and parts arrive and you've assembled everything
   following `guide.txt`, use `file.c` to customize
   [QMK](https://github.com/qmk/qmk_firmware/) for your keyboard.

## Useful Tools, Prior Art, and Guides

* https://github.com/ruiqimao/keyboard-pcb-guide
* http://builder.swillkb.com/
* http://www.keyboard-layout-editor.com/
* https://github.com/fcoury/kbpcb
* https://kbplate.ai03.me/
* https://keebfol.io/tools

## KiCad components and footprints that were copied into here

* `https://github.com/tmk/kicad_lib_tmk`
* `https://github.com/keebio/keebio-components`
* `https://github.com/keebio/Keebio-Parts.pretty`
* `https://github.com/daprice/keyswitches.pretty`
* `https://github.com/tmk/keyboard_parts.pretty`