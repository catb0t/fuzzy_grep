#!/usr/bin/env python3
from string  import punctuation
from difflib import SequenceMatcher as seqman


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


def fuzzy_files(needle, haystack_of_files, tolerance=.4, context_lines=2, punc_is_junk=True, junk_func=None, case_sens=case_sens):

    metamatches = {}

    for f in haystack_of_files:

        t = open(f, "r")
        c = t.read()
        t.close()

        metamatches[f] = fuzzy_grep(
            needle, c, tolerance=tolerance, context_lines=context_lines, punc_is_junk=punc_is_junk, junk_func=junk_func, case_sens=case_sens)

    return metamatches


def fuzzy_grep(needle, haystack, tolerance=.4, context_lines=2, punc_is_junk=True, junk_func=None, case_sens=False):
    """fuzzily grep, finding needle in haystack.split('\n')
    tolerance     = levenshtein tolerance for SequenceMatcher ratio     -- float or int default: .4
    context_lines = lines of context surrounding each match to supply   -- int          default: 2
    punc_is_junk  = whether to consider string.punctuation in fuzziness -- bool         default: True
    junk_func     = a caller-supplied junk-decider                      -- function     default: None
    case_sens     = whether case should be considered in matches        -- bool         default: False"""

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

        if not case_sens:
            line = line.lower()

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

