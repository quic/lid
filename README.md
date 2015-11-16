license_identifier
===

The purpose of this program 'license_identifier' is to scan the source code files and
identify the license text region and the type of license.

Installation
===

Please install python3.  Download the source code from this repository. 

Status
===

[Current Source Code](https://github.qualcomm.com/phshin/license_identifier)

[Wiki - Technical Description and Roadmap](http://qosp-wiki.qualcomm.com/wiki/OS_License_Identification)


Usage
===

```
Please go into ./src folder.

usage: python3 license_identifer folder_name 

will work on these...

optional arguments:
-report        create a summary csv file
-h, --help     show this help message and exit
--version      show program's version number and exit
-T, -threshold set the threshold
-d, -directory
-f FILE
```

If you want to add more licenses, please create a text file with the license text.
Then, save it into the ./src/license_dir folder.
