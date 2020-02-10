# keycad
Generates various CAD files for custom keyboards.

## Installation

* `pip3 install skidl kinjector kinet2pcb`

In a source directory somewhere, clone these repos:

* `https://github.com/tmk/kicad_lib_tmk`
* `https://github.com/keebio/keebio-components`
* `https://github.com/keebio/Keebio-Parts.pretty`
* `https://github.com/daprice/keyswitches.pretty`

* `https://github.com/tmk/keyboard_parts.pretty`

Then you'll need to copy the appropriate .lib files into your
`KICAD_SYMBOL_DIR`. I'm sorry to make you do this, because it'll require `sudo`,
which I try to avoid on my own machines so I don't have to remember how I
configured/broke them. If you know how to make CLI invocations of KiCad pick up
extra global component libraries, let me know.

On my machine, this is what I did:

* `sudo cp ~/src/kicad_lib_tmk/keyboard_parts.lib /usr/share/kicad/library`
* `sudo cp ~/src/keebio-components/keebio.lib /usr/share/kicad/library`

You'll then have to go into the KiCad user interface (Preferences -> Manage
Symbol Libraries) and add the libraries you copied to your global symbol
libraries list. Next, you should go to (Preferences -> Manage Footprint
Libraries) and "add existing library to table" for the
`keebio/Keebio-Parts.pretty` and `daprice/keyswitches.pretty` directories. Use
the suggested nicknames for these items because the code relies on them!

The first time you run `./do_it`, you'll get some errors from Python libraries
that haven't been updated for Python 3. Look at the error messages and then
solve like this:

`2to3-2.7 -w ~/.local/lib/python3.6/site-packages/kinet2pcb/kinet2pcb.py`

and this:

`2to3-2.7 -w ~/.local/lib/python3.6/site-packages/kinjector/cli.py`

Hopefully, your version of `pip3` installed locally so you don't need sudo for this.

Finally, when you have everything installed, you might see an error like this:

`OSError: Expecting "'('" in input/source`

This is [this issue](https://github.com/xesscorp/kinjector/issues/1), and if it
isn't fixed, you should patch your local kinjector installation as I did in
[this patch](https://github.com/xesscorp/kinjector/pull/3/commits/6ad35b76cdccd50c49ad14d9385a7040a896fa83).
(Actually I don't think that fix is right; I ended up putting `raise Exception`
at line 143 to skip the YAML attempt entirely.)

## Useful Tools, Prior Art, and Guides

* https://github.com/ruiqimao/keyboard-pcb-guide
* http://builder.swillkb.com/
* http://www.keyboard-layout-editor.com/
* https://github.com/fcoury/kbpcb