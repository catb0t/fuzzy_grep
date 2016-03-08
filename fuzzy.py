#!/usr/bin/env python3
from __future__ import division
from string  import punctuation as punc
from difflib import SequenceMatcher as seqmat

DEBUG = True

class Match():

    def __init__(self, line, line_no, match_type, prectxt, postctxt, misc=None):
        (self.line, self.line_no,
            self.match_type, self.prectxt,
                self.postctxt, self.misc_data) = (line, line_no,
                                    match_type, prectxt, postctxt, misc)

        self.matchinfo = (self.line, self.line_no, self.match_type,
                          self.prectxt, self.postctxt, self.misc_data)

    def match(self): return self.matchinfo

    def misc(self): return self.misc_data


def is_subset(a, b):
    """a slow (iterative) dupe-preserving sorting "set",
    for mutual membership tests (set overloads &, but removes dupes)"""
    c = []
    a, b = sorted(list(a)), sorted(list(b))
    (l, maxl, s, minl) = {
        True:  (a, len(a), b, len(b)),
        False: (b, len(b), a, len(a))
    }[ a >= b ]

    for i in range(maxl):
        try:
            if s.count(l[i]) >= l.count(l[i]):
                c.append(a[i])

        except IndexError:
            pass
    return c

def fuzzy_files(needle, file_haystack, **kwargs):
    """fuzzy grep in files. turns kwargs in to fuzzy_files"""

    metamatches = {}

    for fname in file_haystack:

        fio = open(fname, "r")
        fct = fio.read()
        fio.close()

        metamatches[fname] = fuzzy_grep(needle, fct, **kwargs)

    return metamatches


def fuzzy_grep(needle,       haystack,
        TOLERANCE_BASE=.3,   CONTEXT_LINES=2,
        PUNC_IS_JUNK=True,   JUNK_FUNC=None,
        CONSIDER_CASE=False, ADJUST_BYLEN=True, APPROX_THRESHOLD=.45):
    """fuzzily grep, finding needle in haystack.split('\n')
    tolerance_base = base levenshtein tolerance for seqman ratio         :float default: .4
    context_lines  = lines of context surrounding each match to supply   :int   default: 2
    punc_is_junk   = whether to consider string.punctuation in fuzziness :bool  default: True
    junk_func      = a caller-supplied junk-decider                      :func  default: None
    case_sens      = should case be considered in matches                :bool  default: False
    adjust_bylen   = adjust tolerance using ratio of needle to line len  :bool  default: True"""

    matches = []

    CONTEXT_LINES += 1

    if PUNC_IS_JUNK:
        junk = (
            lambda x: set(punc) & set(x)
        )
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

        if ADJUST_BYLEN:
            try:
                coef = len(needle) / len(line)
            except ZeroDivisionError:
                coef = 0
            tolerance = round(tolerance + tolerance * (coef * 2), 2)

        fuzziness = is_subset(needle, line)

        s = seqmat(
            junk,
            line,
            needle
        )
        ratio = s.ratio()
        exact = (needle in line) or ("".join(sorted(needle)) in "".join(sorted(line)))
        apprx = ratio + tolerance
        found = exact or apprx > APPROX_THRESHOLD
        #print(round(ratio, 2), round(tolerance, 2), round(apprx, 2), bool(apprx), bool(found))
        if found and fuzziness == sorted(needle):
            try:
                matches.append(
                    Match(
                        line,
                        idx,
                        "exact" if exact else "fuzzy",
                        [ ln for ln in [ ls[idx - i] for i in range(1, CONTEXT_LINES) ] ],
                        [ ln for ln in [ ls[idx + i] for i in range(1, CONTEXT_LINES) ] ],
                        misc={
                            "seqmat": {"self": s, "ratio": ratio, "tolerance": tolerance, "tolerance_base": TOLERANCE_BASE},
                            "misc": locals()
                        }
                    )
                )

            except IndexError:
                pass

    return matches

from sys import argv
def demo():
    output = []
    results = fuzzy_files(argv[1], argv[2:])  # a string as arg #1 and filenames as the rest

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

    print("".join(output))

if __name__ == '__main__' and DEBUG:
    demo()
    print(len(fuzzy_files(argv[1], argv[2:])[argv[2]]))