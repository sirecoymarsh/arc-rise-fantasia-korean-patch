ARFX Readme

This tool was made by me to practice programming. The sourcecode is included in case anyone wants to see this mess or has to fix something.

Features:
-open .vol (RTDP) archives of the game Arc Rise Fantasia for the Wii
-extract content of archives
-reinsert content (regardless of size, header will be rewritten)
-show useful info about the archive file and its content

Known issues:
In the English version of Arc Rise Fantasia -and maybe in the Japanese too- many vol-archives contain files with the name "reserved_file". These files are always 0 bytes in size and at the offset 0x0. This program does not bother about these files and changes their offset in the filetable when a rewrite of the vol-fileheader is needed. But this should be no problem for the game itself since it will not "watch" for these files anyway. This will also have no influence to the filesize of the vol-archive.

Thanks to:
WRS for writing a quickbms-script for these archives. This tool is based on his script.
Berserker for helping me with some issues while coding this tool.

Contact: RetroHelix rhx.retrohelix@googlemail.com