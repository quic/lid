License Identifier
===

The purpose of this program, `license_identifier`, is to scan the source code
files and identify the license text region and the type of license.

Status
===

[![Build Status](https://jenkins.open.qualcomm.com/buildStatus/icon?job=license_identifier)](https://jenkins.open.qualcomm.com/job/license_identifier/)

[Current Source Code](https://github.qualcomm.com/phshin/license_identifier)

[Wiki - Technical Description and Roadmap](http://qosp-wiki.qualcomm.com/wiki/OS_License_Identification)

Installation
===

## Installation for end users and client applications

If you wish to install `license_identifier` as an end user, or if you are
developing an application that depends on `license_identifier`, please install
it as follows:

```
# Set up a virtualenv
virtualenv ENV
source ENV/bin/activate

# Get the latest versions of pip and setuptools:
pip install -U setuptools pip

# Install comment-parser (to prevent pip from finding the wrong package on PyPI)
pip install git+https://github.qualcomm.com/qosp/comment-parser.git@0.2.7

# Install license_identifier
pip install git+https://github.qualcomm.com/qosp/license_identifier.git
```

At this point, you can test the installation by running, for example:
```
license-identifier -I path/to/source/files
```

Note for the developers who want to integrate this module into their code:
The program reads all the license files when it begins - it takes a few seconds.
For efficiency gain, I would recommend instantiating one instance, and running
the `analyze_input_path` method.

## Running under pypy for improved performance

You need a recent version of pypy, only later Ubuntu versions have a sufficiently new version available, e.g. 16.10 onwards. Otherwise you need to install pypy from http://pypy.org.

Once pypy is installed on the system, the only change to the process above is to create the virtualenv specifying the correct interpreter:

```
# Set up a virtualenv
virtualenv -p pypy ENV
source ENV/bin/activate
```

Alternatively if you have pypy installed locally provide the full path to the interpreter.

```
# Set up a virtualenv
virtualenv -p /path_to_pypy_install/bin/pypy ENV
source ENV/bin/activate
```

Then follow the remaining instructions above to install LiD and dependencies into the environment.

You can also use the dockerfile provided to spin up a container with the correct dependencies installed.

## Installation for project maintainers

If you wish to install `license_identifier` for development and testing,
please follow the instructions in this section.

Please use virtualenv:
```
virtualenv ENV
source ENV/bin/activate
pip install -U setuptools pip  # get the latest versions of pip and setuptools
```

To install dependencies:
```
make deps
make test-deps
```

To update the licenses from the web:
```
make update-licenses  # OPTIONAL
```

To generate the default license library as a pickle file:
```
make pickle
```

To run tests:
```
make test
```

Usage
===

```
usage: license-identifier -I '/your/input/file/dir_or_file' -F 'easy_read'

optional arguments:
-T, --threshold     Set the threshold for similarity measure (ranging from 0 to 1, default value is 0.04)
-L, --license_folder    Specify the directory where the license text files are.
-I, --input_path    Specify the input path that needs scanning - to a file or a directory (when pointed to a directory, it considers subdirectories recursively)
-F, --output_format Specify the output format (options are 'csv', 'easy_read')
-O, --output_file_path Specify the output directory and prefix of the file name.  User name, date, time and '.csv' will be added to the file name automatically.  (a must for 'csv' file format option)
-P, --pickle_file_path Specify the file where all the n-gram objects will be stored for the future runs
```

There are four main modes:
```
# 1. Use the default pickled license library file (recommended)
license-identifier -I /path/to/source/code

# 2. Use a particular pickled license library file
license-identifier -P /path/to/pickled_licenses -I /path/to/source_code

# 3. Use a license directory without building a pickled file (please make sure license files have .txt extensions)
license-identifier -L /path/to/license_directory -I /path/to/source_code

# 4. Build a pickled file from the specified license directory
license-identifier -L /path/to/license_directory -P /path/to/output_pickled_licenses
```

## Adding Licenses

If you want to add more licenses, please create a text file with the license text.
Then, save it into the `./data/license_dir/custom` folder.
Then, build the n-gram license library using `make pickle`.
