# album-rsync [![Build Status](https://travis-ci.org/phdesign/album-rsync.svg?branch=master)](https://travis-ci.org/phdesign/album-rsync)

A python script to manage synchronising a local directory of photos with a remote storage provider based on an rsync interaction pattern.

## Requirements

See [requirements.txt](requirements.txt) for list of dependencies.  
Supports Python 3.6+  
For Python 2, see https://github.com/phdesign/flickr-rsync

## Installation

### Via PyPI

Install from the python package manager by
```
$ pip install album-rsync
```

### From GitHub repo

Clone the GitHub repo locally

To install globally:
```
$ python setup.py install
```

To install for the current user only:
```
$ python setup.py install --user
```

## Storage providers

Currently the local file system, Flickr and Google Photos are supported. Below is a list of supported features for each.

|                    | Local | Flickr | Google |
| ------------------ | ----- | ------ | ------ |
| Root files         | Yes   | Yes    | No     |
| Delete extra files | Yes   | Yes    | No     |
| Logout             | No    | Yes    | Yes    |

## Authenticating

To authenticate against a storage provider, you will need to setup API keys, and then authorise your account.

To create API keys, visit:
**Flickr:** https://www.flickr.com/services/api/misc.api_keys.html
**Google:** https://console.developers.google.com/apis/library/photoslibrary.googleapis.com

You will be issued an api key and a secret. To enable the app to use these keys, either:

* For Flickr, provide `--flickr-api-key` and `--flickr-api-secret` arguments to the command line
* For Google, provide `--google-api-key` and `--google-api-secret` arguments to the command line
* create a config file in $HOME/.album-rsync.ini with the following entries

```
# For Flickr
FLICKR_API_KEY = xxxxxxxxxxxxxxxxxxx
FLICKR_API_SECRET = yyyyyyyyyyyyyy

# For Google
GOOGLE_API_KEY = xxxxxxxxxxxxxxxxxxx
GOOGLE_API_SECRET = yyyyyyyyyyyyyy
```

The first time you perform any action against the storage provider, this app will prompt you to authorise access to your account. For Flickr you may choose to request delete permissions, or write only permissions if you do not want any photos deleted by this app.

### Logout

To remove the authentication token for a storage provider, specify the storage provider as the source and pass the `--logout` argument. E.g.

```
$ album-rsync flickr --logout
```

## Listing files

The `--list-only` flag will print a list of files in the source storage provider, this can either be Flickr by specifying the `src` as `flickr`, `google` or a local file system path. Use `--list-sort` to sort the files alphabetically (slower). This feature is useful for manually creating a diff between your local files and Flickr files.

e.g. List all files in Flickr photo sets

```
$ album-rsync flickr --list-only
```

or list sorted files from Google 

```
$ album-rsync google --list-only --list-sort
```

or list all files in a local folder

```
$ album-rsync ~/Pictures --list-only
```

### Tree view vs. csv view

You can change the output from a tree view to a comma separated values view by using `--list-format=tree` or `--list-format=csv`. By default the tree view is used.

e.g. Print in tree format

```
$ album-rsync flickr --list-only --list-format=tree

├─── 2017-04-24 Family Holiday
│   ├─── IMG_2546.jpg [70ebf9]
│   ├─── IMG_2547.jpg [3d3046]
│   ├─── IMG_2548.jpg [2f2385]
│   └─── IMG_2549.jpg [d8e946]
│   
└─── 2017-04-16 Easter Camping
    ├─── IMG_2515.jpg [aabe74]
    ├─── IMG_2516.jpg [0eb4f2]
    └─── IMG_2517.jpg [4fe908]
```

Or csv format

```
$ album-rsync flickr --list-only --list-format=csv

Folder, Filename, Checksum
2017-04-24 Family Holiday, IMG_2546.jpg, 70ebf9be4d8301e94c65582977332754
2017-04-24 Family Holiday, IMG_2547.jpg, 3d3046b37ba338793a762ab7bd83e85c
2017-04-24 Family Holiday, IMG_2548.jpg, 2f23853abeb742551043a3514ba4315b
2017-04-24 Family Holiday, IMG_2549.jpg, d8e946e73700b9c2890d3681c3c0fa0b
2017-04-16 Easter Camping, IMG_2515.jpg, aabe74b06c3a53e801893347eb6bd7f5
2017-04-16 Easter Camping, IMG_2516.jpg, 0eb4f2519f6562ff66069618637a7b10
2017-04-16 Easter Camping, IMG_2517.jpg, 4fe9085b9f320a67988f84e85338a3ff
```

## Listing folders

To just list the top level folders (without all the files). use `--list-folders`. 

```
$ album-rsync ~/Pictures --list-folders
```
## Syncing files

e.g. To copy all files from Flickr to a local folder

```
$ album-rsync flickr ~/Pictures/flickr
```

Or to copy all files from a local folder up to Flickr	

```
$ album-rsync ~/Pictures/flickr flickr
```

You can even copy from a local folder to another local folder

```
$ album-rsync ~/Pictures/from ~/Pictures/to
```

Files are matched by folder names and file names, case insensitively. E.g. if you have a Flickr photoset called `2017-04-16 Easter Camping` and a file called `IMG_2517.jpg`, and you are trying to copy from a folder with `2017-04-16 Easter Camping\IMG_2517.jpg` it will assume this file is the same and will not try to copy it.

### Dry run

Before performing any operations, it's recommended to perform a dry run first, just pass `-n` or `--dry-run` to simulate syncing, without actually copying anything.

### Deleting extra files

>  WARNING: Use of this feature will permanently delete files, be sure you know what you're doing. 

NOTE: Deleting extra files is not supported by the Google storage provider.

Pass `--delete` to delete any extra files from the destination that don't exist in the source. E.g.

```
$ album-rsync ~/Pictures/flickr flickr --delete
```

## Filtering

Filtering is done using regular expressions. The following four options control filtering the files:

* `--include=` specifies a pattern that **file names** must match to be included in the operation
* `--include-dir=` specifies a pattern that **folder names** must match to be included in the operation
* `--exclude=` specifies a pattern that **file names** must NOT match to be included in the operation
* `--exclude-dir=` specifies a pattern that **folder names** must NOT match to be included in the operation

Note that filtering by folders is more performant than by file names, prefer folder name filtering where possible.

Also note that exclude filters take preference and will override include filters.

### Root files

Note that filtering does not apply to root files, root files (files in the target folder if local file system, or files not in a photoset on Flickr) are excluded by default. To include them, use `--root-files`.

## Options

All options can be provided by either editing the config file `album-rsync.ini` or using the command line interface.

```
usage: album-rsync [-h] [-l] [--list-format {tree,csv}] [--list-sort]
                   [--list-folders] [--delete] [-c] [--include REGEX]
                   [--include-dir REGEX] [--exclude REGEX]
                   [--exclude-dir REGEX] [--root-files] [-n]
                   [--throttling SEC] [--retry NUM]
                   [--flickr-api-key FLICKR_API_KEY]
                   [--flickr-api-secret FLICKR_API_SECRET]
                   [--flickr-tags "TAG1 TAG2"]
                   [--google-api-key GOOGLE_API_KEY]
                   [--google-api-secret GOOGLE_API_SECRET] [--logout] [-v]
                   [--version]
                   [src] [dest]

A python script to manage synchronising a local directory of photos with a
remote storage provider based on an rsync interaction pattern.

positional arguments:
  src                   the source directory to copy or list files from, or
                        FLICKR to specify flickr
  dest                  the destination directory to copy files to, or FLICKR
                        to specify flickr

optional arguments:
  -h, --help            show this help message and exit
  -l, --list-only       list the files in --src instead of copying them
  --list-format {tree,csv}
                        output format for --list-only, TREE for a tree based
                        output or CSV
  --list-sort           sort alphabetically when --list-only, note that this
                        forces buffering of remote sources so will be slower
  --list-folders        lists only folders (no files, implies --list-only)
  --delete              WARNING: permanently deletes additional files in
                        destination
  -c, --checksum        calculate file checksums for local files. Print
                        checksum when listing, use checksum for comparison
                        when syncing
  --include REGEX       include only files matching REGEX. Defaults to media
                        file extensions only
  --include-dir REGEX   include only directories matching REGEX
  --exclude REGEX       exclude any files matching REGEX, note this takes
                        precedent over --include
  --exclude-dir REGEX   exclude any directories matching REGEX, note this
                        takes precedent over --include-dir
  --root-files          includes roots files (not in a directory or a
                        photoset) in the list or copy
  -n, --dry-run         in sync mode, don't actually copy anything, just
                        simulate the process and output
  --throttling SEC      the delay in seconds (may be decimal) before each
                        network call
  --retry NUM           the number of times to retry a network call (using
                        exponential backoff) before failing
  --flickr-api-key FLICKR_API_KEY
                        flickr API key
  --flickr-api-secret FLICKR_API_SECRET
                        flickr API secret
  --flickr-tags "TAG1 TAG2"
                        space seperated list of tags to apply to uploaded
                        files on flickr
  --google-api-key GOOGLE_API_KEY
                        Google API key
  --google-api-secret GOOGLE_API_SECRET
                        Google API secret
  --logout              logout of remote storage provider (determined by src)
  -v, --verbose         increase verbosity
  --version             show program's version number and exit
```

### Config and token file discovery

The config file `album-rsync.ini` and token file `album-rsync.token` are searched for in the following locations in order:
* `<current working dir>/album-rsync.ini`
* `<current working dir>/.album-rsync.ini`
* `<users home dir>/album-rsync.ini`
* `<users home dir>/.album-rsync.ini`
* `<executable dir>/album-rsync.ini`
* `<executable dir>/.album-rsync.ini`

The token file is auto generated file containing the authorisation token to access the API. If deleted you will need to authorise the app again when next using it.

## Developing

Install in development mode so source files are symlinked, meaning changes you make to the source files are reflected when you run the package anywhere.
```
$ python setup.py develop
```

Then to uninstall
```
$ python setup.py develop --uninstall
```

## Debugging

Use pdb

```
python -m pdb ./flickr_rsync/__main__.py <parameters>
```

Set a breakpoint

```
b ./flickr_rsync/flickr_storage.py:74
```

Then `c(ontinue)` or `n(ext)` to step over or `s(tep)`  to step into. 

`l(ist)` to show current line and 11 lines of context.

`p(print)` or `pp` (pretty print) to print a variable. E.g.

```
p dir(photo)
pp photo.__dict__
```

To print all properties of variable photo.

`q(uit)` to exit.

Checkout https://medium.com/instamojo-matters/become-a-pdb-power-user-e3fc4e2774b2

## Publishing

Based on [http://peterdowns.com/posts/first-time-with-pypi.html](http://peterdowns.com/posts/first-time-with-pypi.html)

1. Update `album_rsync/_version.py` with the new version number (e.g. 1.1.1)
2. Create a new GitHub release (e.g. `git tag -a v1.1.1 -m "Version v1.1.1" && git push --tags`)
3. Push to PyPI
```
$ make deploy
```

## Running tests

If `make` is installed, you can run tests using a virtual environment

```
$ make venv
$ make test
```

which will lint the code and run tests. To just run the linter

```
$ make lint
```

To run the tests without make, use

```
$ python setup.py test
```

### To mark a focused test

Add decorator `@pytest.mark.focus` to test. Run with

```
$ pytest -m focus
```

## Tips

To list just root files only:
```
$ album-rsync flickr --exclude-dir '.*' --root-files --list-only
```

### Videos
Movies should work, but flickr doesn't seem to return the original video when you download it again, it returns a processed video that may have slightly downgraded quality and will not have the same checksum.

## Troubleshooting

#### I get a Version conflict error with the six python package when installing on my Mac

If you're running Mac OSX El Capitan and you get the following error when running `python setup.py test`

```
pkg_resources.VersionConflict: (six 1.4.1 (/System/Library/Frameworks/Python.fra
mework/Versions/2.7/Extras/lib/python), Requirement.parse('six>=1.9'))
```

Do the following:
```
$ sudo pip install --ignore-installed six
```

More details [https://github.com/pypa/pip/issues/3165](https://github.com/pypa/pip/issues/3165)

#### I get an error 'The Flickr API keys have not been set'

To access Flickr this application needs API keys, go to http://www.flickr.com/services/apps/create/apply to sign up for a free personal API key

#### I get an error 'The Flickr API keys have not been set' but I've set them in my config (ini) file

Getting an error `The Flickr API keys have not been set` but you've set them in the config file? Perhaps the application can't find the config file location. Use `-v` or `--verbose` option to print the location of the config file being used.

#### Why are some files are not being shown in the file list / sync?

By default only media files are included in file listings and sync operations. Media files are defined as `\.(jpg|jpeg|png|gif|tiff|tif|bmp|psd|svg|raw|wmv|avi|mov|mpg|mp4|3gp|ogg|ogv|m2ts)$`. Use `--include=.*` to include all files.

#### I get an error 'The filename, directory name or volume label syntax is incorrect'

If you're seeing an error like this

```
WindowsError: [Error 123] The filename, directory name, or volume label syntax is incorrect: 'C:\\Users\\xxx\\Pictures" --list-only/*.*'
```

Ensure that you are not using single quotes `'` around a folder path in windows, instead use double quotes `"`. e.g.

```
$ album-rsync "C:\Users\xxx\Pictures" --list-only
```

#### When I try list list in a local folder called 'flickr' it lists my remote flickr files

album-rsync uses the keyword `flickr` as a src or dest to denote pulling the list from flickr. If you have a folder called flickr, just give it a relative or absolute path make it obvious that it's a file path, e.g.

```
$ album-rsync ./flickr --list-only
```

#### If I add tags, they get changed by flickr, e.g. 'extn=mov becomes extnmov'.
Internally flickr removes all whitespace and special characters, so 'extn mov' and 'extn=mov' match 'extnmov'. You can 
edit a tag using this URL:
https://www.flickr.com/photos/{username}/tags/{tagname}/edit/
or go here to manage all tags:
https://www.flickr.com/photos/{username}/tags
And in future put double quotes around your tag to retain special characters

#### I get an error 'UnicodeEncodeError: 'charmap' codec can't encode characters in position 0-3: character maps to \<undefined\>'

This error occurs on Windows when you redirect stdout. To fix this, set PYTHONIOENCODING=utf-8. e.g.

```
$ PYTHONIOENCODING=utf-8 album-rsync ./flickr --list-only
```

## Release notes

### v2.0.4 (14 Mar 2019)

* Renamed to `album-rsync`
* Converted to Python 3
* Added Google Photos storage provider
* Continues to next file when an error occurs copying a file (after retry policies have been applied)
* Support for deleting extra files in destination

### v1.0.5 (21 Mar 2018)

* Support for videos
* Add tag to maintain original extension 

### v1.0.4 (2 Nov 2017)
* Improve retry and throttling, now uses exponential backoff
* Use python logging framework, outputs log messages to stderr

### v1.0.3 (16 Sep 2017)
* Flickr converts .jpeg to .jpg extensions, so consider them the same when comparing for sync


## TODO

- [ ] Handle nested directories. Merge with separator like `parent_child`. Apply --include-dir after merging
- [ ] List duplicate files
- [ ] Webpage for successful Flickr login
- [ ] Optimise - why does sort files seem to run faster?!
- [ ] Fix duplicate albums issue
- [ ] Why does it make 3 api calls for every photo in --list-only --list-sort mode?
- [ ] --init to setup a new .ini file and walk through auth process
- [ ] Add throttling and delay to Google
