# lst2bin_iso
Converts the images created from the CDVDGEN tool (CDVDREC) into normal .bin/iso images

This code was initially based on the one from user "Cut Into Fourteen Pieces" at https://www.obscuregamers.com/threads/how-to-create-a-working-playstation-2-master-cd-r-or-dvd-r-image.772/post-17636.html

Pre-compiled releases of this code can be downloaded from here:

https://github.com/N4gtan/lst2bin_iso/releases/latest

# Features
This script can generate valid DVD (M1/2048) and CD (M2/2352) images from the .lst files that outputs CDVDREC.

Also it can regenerate or erease EDC/ECC from PSX/PS2 CD image files (.bin/img)

# Usage
```
lst2bin_iso.exe [-nm] [-nf2] [-b] input_file [output_file]
```
Or you can simply drag and drop a supported file type into the executable file

## Commands:
Required:
```
input_file       supported files .lst/000/bin/img
```
Optionals:
```
output_file      optional output file path
-nm, --nomaster  zeroes master disc sectors
-nf2, --noform2  zeroes form2 EDC and regens form1 EDC/ECC
-b, --blank      zeroes form1 and form2 EDC/ECC
```

Example:
```
lst2bin_iso.exe -nm image.lst
```

Notes:

If no argument is specified, defaults to make an .iso for DVD or a .bin/cue for CD images (also regens EDC/ECC)

.000 files are only supported for CD images and defaults to an .bin/cue file (also regens EDC/ECC)

.bin/img files are for use with arguments, if no argument is specified defaults to regen it's EDC/ECC

# Compile
If you will want to use the script instead of the executable first you will need to compile the Cython module

Install Cython:
```
pip install cython
```

Then navigate to the source files directory and run:
```
python setup.py build_ext --inplace
```

This will compile the Cython .pyx file into a .so (or .pyd on Windows) module for use along with the lst2bin_iso.py script

Note: You will need to have installed a C compiler, so follow the instruccions in Cython to install it for your system.
