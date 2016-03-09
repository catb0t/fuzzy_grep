#!/usr/bin/env python3
from string  import punctuation
from difflib import SequenceMatcher as seqman

DEBUG = True

class Match():

    def __init__(self, line, line_no, match_type, prectxt, postctxt, misc=None):
        self.line, self.line_no, self.match_type, self.prectxt, self.postctxt = line, line_no, match_type, prectxt, postctxt

        self.misc_data = misc

        self.matchinfo = (self.line, self.line_no, self.match_type,
                          self.prectxt, self.postctxt, self.misc_data)

    def match(self): return self.matchinfo

    def misc(self): return self.misc_data


def _sort_and_join(s):
    x = set("".join(sorted(set(list(s)))))
    return [x, "".join(x)]


def slowset(a, b):
    """a slow (iterative) dupe-preserving sorting "set",
    for mutual membership tests (set overloads &, but removes dupes)"""
    c = []
    a, b = sorted(list(a)), sorted(list(b))
    for i in range(max(len(a), len(b))):
        try:
            if (a[i] == b[i]) and (a.count(a[i]) == b.count(b[i])):
                c.append(a[i])
        except IndexError:
            pass
    return c

def fuzzy_files(needle, haystack_of_files, **kwargs):

    metamatches = {}

    for f in haystack_of_files:

        t = open(f, "r")
        c = t.read()
        t.close()

        metamatches[f] = fuzzy_grep(
            needle, c, **kwargs)

    return metamatches


def fuzzy_grep(needle,     haystack,
        tolerance_base=.4,      context_lines=2,
        punc_is_junk=True, junk_func=None,
        case_sens=False,   adjust_bylen=True):
    """fuzzily grep, finding needle in haystack.split('\n')
    tolerance_base = base levenshtein tolerance for seqman ratio         -- float or int default: .4
    context_lines  = lines of context surrounding each match to supply   -- int          default: 2
    punc_is_junk   = whether to consider string.punctuation in fuzziness -- bool         default: True
    junk_func      = a caller-supplied junk-decider                      -- function     default: None
    case_sens      = should case be considered in matches                -- bool         default: False
    adjust_bylen   = adjust tolerance using ratio of needle to line len  -- bool         default: True"""

    matches = []

    if not case_sens:
        needle = needle.lower()

    if punc_is_junk:
        junk = lambda x: set(punctuation) & set(x)
    elif junk_func:
        junk = junk_func
    else:
        junk = lambda x: False

    s_txt, js_txt = _sort_and_join(needle)

    lns = haystack.split("\n")

    for num, line in enumerate(lns):

        tolerance = tolerance_base

        if not case_sens:
            line = line.lower()

        if adjust_bylen:
            try:
                coef = len(needle) / len(line)
            except ZeroDivisionError:
                coef = .5
            tolerance += tolerance * coef
            print(tolerance)

        s_line, _ = _sort_and_join(line)

        hasletters = "".join(s_txt & s_line)

        s = seqman(
            junk,
            line,
            needle
        )

        ratio  = s.ratio()
        exact  = needle in line
        approx = round(ratio + tolerance)
        found  = exact or approx
        if found and hasletters == js_txt:
            try:
                matches.append(
                    Match(
                        line,
                        num,
                        "exact" if exact else "fuzzy",
                        [ ln for ln in [ lns[num - i] for i in range(1, context_lines) ] ],
                        [ ln for ln in [ lns[num + i] for i in range(1, context_lines) ] ],
                        misc={
                            "seqman": {"self": s, "ratio": ratio, "tolerance": tolerance},
                            "misc": {
                                "exact": exact, "approx": approx, "found": found, "context_lines": context_lines,
                                "punc_is_junk": punc_is_junk, "junk_func": junk_func, "junk_decider": junk,
                                "sorted_txt": s_txt, "sorted_line": s_line, "line_has_letters": hasletters,
                            }
                        }
                    )
                )

            except IndexError:
                pass

    return matches

def demo():
    from sys import argv
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
                ">>>\t" + item.line + "\n" +
                "\t" + "\n\t".join(item.postctxt) + "\n"
            )

    print("".join(output))

if __name__ == '__main__' and DEBUG:
    demo()