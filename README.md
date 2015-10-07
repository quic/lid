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

optional arguments:
-h, --help     show this help message and exit
--version      show program's version number and exit
-f FILE
```

If you want to add more licenses, please create a text file with the license text.
Then, save it into the ./src/license_dir folder.

To verify the file is valid YAML, contains the expected fields, and
the field values are in the expected format.

```bash
$ codebom lint
```

Use the `scan` command to traverse the current directory looking for missing
declarations.

```bash
$ codebom scan
```

Finally, to verify the BoM is consistent with the code in the current directory,
use the `verify` command:

```bash
$ codebom verify
```


Tucking away the BoM
---

By default, codebom looks for a file `.bom.yaml` in the current directory.
To specify a different location, use the `-f` flag. codebom will interpret
the file from the directory containing that file.

Alternatively, to direct codebom to a BoM at a different location, use
a path to a BoM file anywhere you might declare the contents for a
directory.

```yaml
qosp/codebom/bom.yaml
```

Nested BoMs
---

BoMs may reference other BoMs. In the `dependencies` or
`development-dependencies` section, codebom will look for a `.bom.yaml` file in
the `root` directory.

```yaml
dependencies:
- src/lua
```

Or specify the BoM explicitly:

```yaml
dependencies:
- src/lua/.bom.yaml
```

If `src/lua` contains the following BoM:

```yaml
license: MIT
```

Then codebom can generate a single merged BoM by specifying an output file:

```bash
$ codebom verify -o my-lua-app.yaml
$ cat my-lua-app.yaml
--- # Bill of Materials
license: Unknown
dependencies:
- root: src/lua
license: MIT
```

Declaring your origins
---

If you specify an origin URI, codebom will download it and verify its contents
match the files in the `root`. If the URI points to a file, codebom will
verify `root` points to a file as well and the file contents match.

```yaml
--- # Bill of Materials
dependencies:
- root: lua/lua-5.3.0
origin: http://www.lua.org/ftp/lua-5.3.0.tar.gz
license: MIT
license-file: doc/readme.html
- root: sha1/sha1.c
origin: http://www.ghostscript.com/doc/jbig2dec/sha1.c
license: PublicDomain
forked: true
```

Setting the `forked` property tells codebom not to expect the file contents
to match. It exists so that you can *always* declare an `origin` for your open
source dependencies.


Licenses
---

```
GPL <version>       GNU Public License
LGPL <version>      Lesser GPL
BSD3                3-clause BSD license
BSD4                4-clause BSD license
MIT                 The MIT license
Apache <version>    The Apache License
PublicDomain        Holder makes no claim to ownership
AllRightsReserved   No rights are granted to others
Other <string>      Name of some other license
Unknown             License is unknown
```
