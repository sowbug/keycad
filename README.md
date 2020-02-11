# keycad

Generates KiCad PCBs for custom keyboards.

## Installation

* `sudo apt install kicad`  (or however you install KiCad on your system)
* `pip3 install skidl kinjector kinet2pcb`

Then in KiCad under Preferences -> Manage Symbol Libraries, add the keycad.lib
file as a global library, and then in Preferences -> Manage Symbol Libraries add
the keycad.pretty/ directory as a global footprint library.

When you have everything installed and run `./do_it`, you might see an error like this:

`OSError: Expecting "'('" in input/source`

This is [this issue](https://github.com/xesscorp/kinjector/issues/1), and if it
isn't fixed, you should patch your local kinjector installation as I did in
[this patch](https://github.com/xesscorp/kinjector/pull/3/commits/6ad35b76cdccd50c49ad14d9385a7040a896fa83).

## Useful Tools, Prior Art, and Guides

* https://github.com/ruiqimao/keyboard-pcb-guide
* http://builder.swillkb.com/
* http://www.keyboard-layout-editor.com/
* https://github.com/fcoury/kbpcb

## KiCad components and footprints that were copied into here

* `https://github.com/tmk/kicad_lib_tmk`
* `https://github.com/keebio/keebio-components`
* `https://github.com/keebio/Keebio-Parts.pretty`
* `https://github.com/daprice/keyswitches.pretty`
* `https://github.com/tmk/keyboard_parts.pretty`