license_identifier
===

The purpose of this program 'license_identifier' is to scan the source code files and
identify the license text region and the type of license.

[![Build Status](https://jenkins.open.qualcomm.com/buildStatus/icon?job=license_identifier)](https://jenkins.open.qualcomm.com/job/license_identifier/)

Installation
===

Please use virtual env:
```
virtualenv ENV
source ENV/bin/activate
```

To install dependencies:
```
make deps
make test-deps
```

To run tests:

```
make test
```

Status
===

[Current Source Code](https://github.qualcomm.com/phshin/license_identifier)

[Wiki - Technical Description and Roadmap](http://qosp-wiki.qualcomm.com/wiki/OS_License_Identification)


Usage
===

```
Please specify the input directory when running the program.

usage: python -m license_identifier.license_identifier -I '/your/input/file/dir_or_file' -F 'easy_read'

optional arguments:
-T, --threshold     Set the threshold for similarity measure (ranging from 0 to 1, default value is 0.04)
-L, --license_folder    Specify the directory where the license text files are.
-I, --input_path    Specify the input path that needs scanning - to a file or a directory (when pointed to a directory, it considers subdirectories recursively)
-F, --output_format Specify the output format (options are 'csv', 'easy_read')
-O, --output_file_path Specify the output directory and prefix of the file name.  User name, date, time and '.csv' will be added to the file name automatically.  (a must for 'csv' file format option)
-P, --pickle_file_path Specify the file where all the n-gram objects will be stored for the future runs
```

If you want to add more licenses, please create a text file with the license text.
Then, save it into the ./data/license_dir/custom folder.
Then, build the n-gram license library using the following command.

usage: python -m license_identifier.license_identifier -L 'my_license_dir/license_dir' -P 'my_pickle_file.pickle'

For advanced user, there are three modes of running the tool:
1. Use the pickled library file.
By default, if the -P or -L are not set, it will use default pickled file.  If the user wants to specify
the pickled file, please use -P option.

2. Use license directory without building a pickled file.
Please use -L to specify the location of the license file directory.

3. Build a pickled file from the specified license directory.
Please name the new pickled file using -P option, and use -L option to specify where the directory where the license template files are.

Note for the developers who want to integrate this module into their code.
The program reads all the license files when it begins - it takes a few seconds.  For efficiency gain,
I would recommend instantiating one instance, and running analyze_input_path method.

