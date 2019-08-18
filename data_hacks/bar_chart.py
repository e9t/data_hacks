#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2010 Bitly
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""
Generate an ascii bar chart for input data

https://github.com/bitly/data_hacks
"""
import sys
import math
from collections import defaultdict
from optparse import OptionParser
from decimal import Decimal
import unicodedata


def load_stream(input_stream):
    for line in input_stream:
        clean_line = line.strip()
        if not clean_line:
            # skip empty lines (ie: newlines)
            continue
        if clean_line[0] in ['"', "'"]:
            clean_line = clean_line.strip('"').strip("'")
        if clean_line:
            yield clean_line


def run(input_stream, options, encoding='utf8'):
    options.dot = options.dot.decode(encoding)
    data = defaultdict(int)
    total = 0
    type_ = float
    for row in input_stream:
        if options.agg_key_value:
            kv = row.rstrip().rsplit(None, 1)
            if kv[1].isdigit():
                type_ = int
            value = type_(kv[1])
            data[kv[0].decode(encoding)] += value
            total += value
        elif options.agg_value_key:
            kv = row.lstrip().split(None, 1)
            if kv[0].isdigit():
                type_ = int
            value = type_(kv[0])
            data[kv[1].decode(encoding)] += value
            total += value
        else:
            row = row.decode(encoding)
            data[row] += 1
            total += 1

    if not data:
        print "Error: no data"
        sys.exit(1)

    max_length = max([len(key) for key in data.keys()])
    max_length = min(max_length, int(options.max_key_length))
    value_characters = int(options.max_key_length) + 30 - max_length
    max_value = max(data.values())
    scale = int(math.ceil(float(max_value) / value_characters))
    scale = max(1, scale)

    print ("# each " + options.dot + " represents a count of %d. total %d" % (scale, total)).encode(encoding)

    if options.sort_values:
        data = [[v, k] for k, v in data.items()]
        data.sort(key=lambda x: x[0], reverse=options.reverse_sort)
    else:
        # sort by keys
        data = [[v, k] for k, v in data.items()]
        if options.numeric_sort:
            # keys could be numeric too
            data.sort(key=lambda x: (Decimal(x[1])), reverse=options.reverse_sort)
        else:
            data.sort(key=lambda x: x[1], reverse=options.reverse_sort)

    percentage = ""
    if options.lines:
        nlines = int(options.lines)
    else:
        nlines = None
    for value, key in data[:nlines]:
        if options.percentage:
            percentage = " (%0.2f%%)" % (100 * Decimal(value) / Decimal(total))
        name = [(c, len(c) + sum(1 for d in c if unicodedata.east_asian_width(d) == 'W')) for c in key]
        title = u''
        cum = 0
        for c, l in name:
            cum += l
            if cum <= max_length:
                title += c
            else:
                break

        pad = u' ' * (max_length - cum)

        if isinstance(value, int):
            formatted_string = "%s%s [%6d] %s%s"
        else:
            formatted_string = "%s%s [%6.2f] %s%s"
        print (formatted_string %
               (pad, title[:max_length], value, int(value / scale) * options.dot, percentage))\
            .encode(encoding)


if __name__ == "__main__":
    parser = OptionParser()
    parser.usage = "cat data | %prog [options]"
    parser.add_option("-a", "--agg", dest="agg_value_key", default=False, action="store_true",
                      help="Two column input format, space seperated with value<space>key")
    parser.add_option("-A", "--agg-key-value", dest="agg_key_value", default=False, action="store_true",
                      help="Two column input format, space seperated with key<space>value")
    parser.add_option("-k", "--sort-keys", dest="sort_keys", default=True, action="store_true",
                      help="sort by the key [default]")
    parser.add_option("-v", "--sort-values", dest="sort_values", default=False, action="store_true",
                      help="sort by the frequence")
    parser.add_option("-r", "--reverse-sort", dest="reverse_sort", default=False, action="store_true",
                      help="reverse the sort")
    parser.add_option("-n", "--numeric-sort", dest="numeric_sort", default=False, action="store_true",
                      help="sort keys by numeric sequencing")
    parser.add_option("-p", "--percentage", dest="percentage", default=False, action="store_true",
                      help="List percentage for each bar")
    parser.add_option("-l", "--lines", dest="lines", default=None,
                      help="Maximum number of lines")
    parser.add_option("-m", "--max-key-length", dest="max_key_length", default=50,
                      help="Maximum length of key")
    parser.add_option("--dot", dest="dot", default='∎', help="Dot representation")

    (options, args) = parser.parse_args()

    if sys.stdin.isatty():
        parser.print_usage()
        print "for more help use --help"
        sys.exit(1)
    run(load_stream(sys.stdin), options)
