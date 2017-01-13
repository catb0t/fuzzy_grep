#!/usr/bin/env python3
from __future__ import division
from string  import punctuation as punc
from difflib import SequenceMatcher as seqmat

DEBUG = True

class Match():

    def __init__(self, line, line_no, match_type,
                 prectxt, postctxt, misc=None):
        (self.line, self.line_no,
            self.match_type, self.prectxt,
                self.postctxt, self.misc_data) = (line, line_no,
                                    match_type, prectxt, postctxt, misc)

        self.matchinfo = (self.line, self.line_no, self.match_type,
                          self.prectxt, self.postctxt, self.misc_data)

    def match(self): return self.matchinfo

    def misc(self):  return self.misc_data


def fuzzy_files(needle, file_haystack, **kwargs):
    """fuzzy grep in files. turns kwargs in to fuzzy_files"""

    metamatches = {}

    for fname in file_haystack:

        fio = open(fname, "r")
        fct = fio.read()
        fio.close()

        metamatches[fname] = fuzzy_grep(needle, fct, **kwargs)

    return metamatches


def fuzzy_grep(needle,            haystack,
        TOLERANCE_BASE   = .3,    CONTEXT_LINES = 2,
        PUNC_IS_JUNK     = True,  JUNK_FUNC     = None,
        CONSIDER_CASE    = False, ADJUST_BYLEN  = True,
        APPROX_THRESHOLD = .5
        ):
    """fuzzily grep, finding needle in haystack.split('\n')
    warn: if these aren't properly tweaked, results will be 2fuzzy4u

    KWARG_CONSTANT   = description                          type  = default
    TOLERANCE_BASE   = base tolerance for seqmat ratio      float = .4
    CONTEXT_LINES    = lines surrounding each match to give int   = 2
    PUNC_IS_JUNK     = consider punctuation in fuzziness    bool  = True
    JUNK_FUNC        = a caller-supplied junk-decider       func  = None
    CONSIDER_CASE    = consider case in matches             bool  = False
    ADJUST_BYLEN     = adjust using line len                bool  = True
    APPROX_THRESHOLD = fuzziness threshold; tweak me!       float = .5?
    """

    from collections import Counter

    matches = []

    # case-preserver, for printing lines of context.
    PCASE = {
        "needle": needle,
        "haystack": haystack,
        "haystack_spl": haystack.split("\n"),
    }

    # caching
    # the length of the needle won't change,
    # but the length of the line will,
    # and the same input line len will yield the same output
    ndl_len = len(needle)
    bylen_vals = {}

    # human-usability - the range is from 1 to n, so increment n.
    R_CONTEXT_LINES = range(1, CONTEXT_LINES + 1)

    if PUNC_IS_JUNK:
        junk = (lambda x: set(punc) & set(x))
    elif JUNK_FUNC is not None:
        junk = JUNK_FUNC
    else:
        junk = (lambda x: False)

    if not CONSIDER_CASE:
        needle   = needle.lower()
        haystack = haystack.lower()

    ls = haystack.split("\n")

    for idx, line in enumerate(ls):

        tolerance = TOLERANCE_BASE

        if ADJUST_BYLEN and ndl_len:
            hstk = len(line)
            # caching
            if hstk in bylen_vals.keys():
                tolerance = bylen_vals[hstk]
            elif hstk:
                # seems to be a good algorithm for adjustment based on line len
                tolerance = round(tolerance + tolerance * ((ndl_len / hstk) * 4), 2)
                bylen_vals[hstk] = tolerance

        # nondeduplicating membership tester, like set()
        fuzziness = list((Counter(needle) & Counter(line)).elements())

        s = seqmat(junk, line, needle)

        ratio = s.ratio()
        exact = (needle in line) or ("".join(sorted(needle)) in "".join(sorted(line)))
        apprx = ratio + tolerance
        found = exact or apprx > APPROX_THRESHOLD
        inlin = sorted(fuzziness) == sorted(needle)
        if found and inlin:

            # object-existence insurance; not pointless
            prectxt, postctxt = ([""], [""])

            if (idx - 1) >= 0:
                prectxt = []
                for i in R_CONTEXT_LINES:
                    if idx - i >= 0:
                        prectxt.append(PCASE["haystack_spl"][idx - i])

            if (idx + 1) <= len(ls):
                postctxt = []
                for i in R_CONTEXT_LINES:
                    if idx + i <= len(ls):
                        postctxt.append(PCASE["haystack_spl"][idx + i])

            matches.append(
                Match(
                    line, idx,
                    "exact" if exact else "fuzzy",
                    prectxt, postctxt,
                    misc = {
                        "seqmat": {"self": s, "ratio": ratio, "tolerance": tolerance, "tolerance_base": TOLERANCE_BASE},
                        "misc": locals()
                    }
                )
            )

    return matches

def demo():
    output = []
    needle, haystacks = argv[1], argv[2].split(" ")
    results = fuzzy_files(needle, haystacks)  # a string as arg #1 and filenames as the rest

    for idx, fname in enumerate(results):
        ms = results[fname]

        for item in ms:

            output.append(
                "\n{}\nline {} of file {}: match type = {}\n"
                .format(
                    "-" * 100, item.line_no, fname, item.match_type
                ) + "\n" +
                "\t" + "\n\t".join(item.prectxt) + "\n"
                "\x1b[1;31m>>>\t" + item.line + "\x1b[m\n" +
                "\t" + "\n\t".join(item.postctxt) + "\n"
            )

    print("".join(output), "\n{}\nprocessed {} matches".format("-" * 100, len(output)))

if __name__ == '__main__' and DEBUG:
    from sys import argv
    #print(argv[1], argv[2:])
    demo()
