# Differential backup tool

[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/release)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/nierja/sync/blob/master/LICENSE)

## Overview

Something about this project

## Features

- TODO 
- TODO
- Collored CLI printing

<pre><code>$ ./src/sync.py # SAMPLE OUTPUT MESSAGES
<span style="color:blue">[ CREATE ]</span> ENTITY PATH
<span style="color:green">[ COPY   ]</span> ENTITY PATH TO DEST_PATH
<span style="color:#aeb32e">[ UPDATE ]</span> ENTITY PATH
<span style="color:orange">[ DELETE ]</span> ENTITY PATH 
<span style="color:#ff834e">[ WARN   ]</span> ENTITY WARNING_MESSAGE
<span style="color:red">[ ERROR  ]</span> ENTITY ERROR_MESSAGE
[ SYNCH  ]
</code></pre>

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Results](#results)

## Installation

TODO

## Usage



```shell
$ ./sync.py --help
usage: ./sync.py [-h] [--source SOURCE] [--replica REPLICA] 
                 [--logDir LOGDIR] [--logFileName LOGFILENAME] 
                 [--syncPeriod SYNCPERIOD]

options:
  -h, --help            show this help message and exit
  --source SOURCE       Path to the source directory to be 
                        mirrored
  --replica REPLICA     Pyth to the copy of the source directory
  --logDir LOGDIR       Directory where to store the log file
  --logFileName LOGFILENAME
                        Name of the log file
  --syncPeriod SYNCPERIOD
                        Time interval in seconds between 
                        periodic synchronizations
```