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
Please specify the input directory when running the program.

usage: python3 license_identifier.license_identifer -I '/your/input/file/dir_or_file'

optional arguments:
-T, --threshold     Set the threshold for similarity measure (ranging from 0 to 1)
-L, --license_folder    Specify the directory where the license text files are.
-I, --input_path    Specify the input path - to a file or a directory (when pointed to a directory, it considers subdirectories recursively)
-F, --output_format Specify the output format (options are 'csv', 'license_match', 'easy_read')
-O, --output_filepath Specify the output files (for 'csv' file format option)
```

If you want to add more licenses, please create a text file with the license text.
Then, save it into the ./data/license_dir folder.

Note for the developers who want to integrate this module into their code.
The program is
