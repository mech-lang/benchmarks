"""Unprepared, exact-source owner decisions; never a general Rebol/C parser.

Every numbered row is explicit. Blank rows are the only implicit rows. Hashes
remain unset until the source-only proposal has been executed and reviewed.
The helpers below abbreviate ledger notation; they do not inspect source.
"""

RULE = 'canonical-source-units-20261012-approved-rule-v2'
BASE = 'archive/languages/rebol/20261013/drafts/private-v1/'
CORRECTED_C = 'experiments/rebol/extension-api-v2/clbg_primitives.c'
ORIGINAL_C = BASE + 'support/clbg_primitives.c'
CORRECTED_FANN = 'experiments/rebol/fannkuch-zero-v1/main.reb'
ORIGINAL_FANN = BASE + 'sources/fannkuchredux/main.reb'

# H: explicit header, O: executable opener (zero), C: written close,
# S: independent statement/binding, V: reviewed composed value,
# D: retained physical literal/data row, P: semantic directive,
# E: independently declared enum constant, M: comment (zero).
KINDS = {
    'H': ('explicit-header', 1), 'O': ('written-open', 0),
    'C': ('written-close', 1), 'S': ('independent-statement-or-binding', 1),
    'V': ('source-specific-composed-value', 1), 'D': ('literal-data-row', 1),
    'P': ('semantic-preprocessor-directive', 1), 'E': ('enum-constant', 1),
    'M': ('comment', 0),
}


def parts(*items):
    return tuple(items)


def block(header, *body):
    """One explicitly written Rebol block; body fragments are independent."""
    return parts(('H', header), ('O', '['),
                 *(('S', text) for text in body), ('C', ']'))


def c_if(header, statement):
    return parts(('H', header), ('S', statement))


def source(path, lines, *, rows, headers=(), raw_headers=(), packed=None):
    return dict(path=path, expected_line_count=lines, reviewed_source_sha256=None,
                rows=rows, headers=tuple(headers), raw_headers=tuple(raw_headers),
                packed={} if packed is None else packed)


def main(name, lines, **kwargs):
    return source(BASE + 'sources/' + name + '/main.reb', lines, **kwargs)


SOURCES = {
    'binarytrees': main('binarytrees', 35,
        rows={'D': '1', 'S': '2 5 7-8 10 17-26 28-29 31-32 34-35',
              'V': '14', 'C': '9 11 15 33'},
        headers=(4, 6, 13, 27), packed={
            30: block('loop iterations', 'total: total + (check-tree make-tree depth)'),
        }),
    'fannkuchredux': source(CORRECTED_FANN, 50,
        rows={'D': '1', 'S': '2-3 5-6 9-11 13-14 16-17 19-23 25 28-29 31-32 35-36 38-39 41-42 44-45 50',
              'V': '7 27', 'C': '24 26 40 46-49'},
        headers=(12, 15, 18, 30, 33, 37), packed={
            4: block('if any [n < 0 n > 12]', 'io/fail "Fannkuch size must be in 0..12"'),
            8: block('repeat index n', 'append permutation (index - 1)',
                     'append rotations 0', 'total: total * index'),
            34: block('if width > n', 'io/fail "Unexpected permutation carry"'),
            43: parts(('H', 'either count < width'), ('O', '['),
                      ('S', 'poke rotations width count'), ('S', 'carried: false'),
                      ('C', ']'), ('O', '[')),
        }),
    'fasta': main('fasta', 55,
        rows={'D': '1 3-6', 'S': '2 9-10 12 16-17 19-20 22 30 32-34 36 38-40 44 47-55',
              'C': '13 24 26 37 42 45'},
        headers=(8, 15, 18, (28, 29), 31, 35), packed={
            11: block('foreach [code probability] probabilities',
                      'total: total + probability', 'append result code', 'append result total'),
            21: block('if position > length? alu', 'position: 1'),
            23: block('if column = 60', 'append output 10', 'column: 0'),
            25: block('if column > 0', 'append output 10'),
            41: block('if column = 60', 'append output 10', 'column: 0'),
            43: block('if column > 0', 'append output 10'),
        }),
    'knucleotide': main('knucleotide', 92,
        rows={'D': '1 3', 'S': '2 4 11 13 15 17 21 23 25-28 30 34-35 40-41 43 45-46 54 59 63 65 68-69 72-75 77-78 80 83-85 87-89 92',
              'V': '7 79 90', 'C': '8 16 18 29 31 44 50-53 55 64 66 81-82 91'},
        headers=(6, 10, 12, 20, 24, 33, 36, 37, 38, 42, 48, (57, 58), 62, 71, 76, 86),
        packed={
            14: block('if none? code', 'io/fail "Non-ACGT K sequence byte"'),
            22: block('loop width', 'append result 65'),
            39: block('if selected', 'break'),
            47: parts(('C', ']'), ('O', '[')),
            49: block('foreach byte line',
                      'append sequence (either all [byte >= 97 byte <= 122] [byte - 32] [byte])'),
            60: block('foreach [key count] table',
                      'append/only entries (reduce [(decode-word key width) count])'),
            61: parts(('H', 'sort/compare entries func [left right]'), ('O', '['),
                      ('V', 'either left/2 = right/2 [left/1 < right/1] [left/2 > right/2]'), ('C', ']')),
            70: block('foreach width widths', 'append/only tables (make map! [])'),
        }),
    'mandelbrot': main('mandelbrot', 37,
        rows={'D': '1', 'S': '2-6 8-11 13-18 20-24 27 29 33 35 37',
              'V': '26', 'C': '25 30 34 36'},
        headers=(7, 12, 19, 31), packed={
            28: block('if bits = 8', 'append output byte', 'byte: 0', 'bits: 0'),
            32: block('loop (8 - bits)', 'byte: byte * 2'),
        }),
    'nbody': main('nbody', 80,
        rows={'D': '1 59-70', 'S': '2-4 7 11-12 14-17 19-25 27 29 33 35-36 38-43 45-48 50 52 74 76-77 79-80',
              'C': '8 26 28 30 49 51 53 56-57 73'},
        headers=(6, 10, 13, 18, 32, 34, 37, 44, 54, 71), packed={
            55: block('repeat axis 3', 'poke left axis ((pick left axis) + (0.01 * (pick left (axis + 3))))'),
            72: block('repeat axis 3', 'poke momentum axis ((pick momentum axis) + ((pick body (axis + 3)) * body/7))'),
            75: block('repeat axis 3', 'poke sun (axis + 3) ((negate pick momentum axis) / solar-mass)'),
            78: block('loop n', 'advance bodies'),
        }),
    'pidigits': main('pidigits', 46,
        rows={'D': '1', 'S': '2-11 13-16 18 20-22 24-25 27-30 32-39 44 46',
              'C': '26 40-41 45'},
        headers=(12, 17, 23, 42), packed={
            19: block('if any [digit < 0 digit > 9]', 'io/fail "Invalid spigot digit"'),
            31: parts(('C', ']'), ('O', '[')),
            43: block('loop (10 - column)', 'append output 32'),
        }),
    'regexredux': main('regexredux', 59,
        rows={'D': '1 30-47', 'S': '2-3 6-7 10-11 13 18-19 22-24 26-27 48-50 52 54 56 58-59',
              'C': '12 14 25 28 53 57'},
        headers=(5, 8, (16, 17), 20, 51, 55), packed={
            9: block('if hit/2 <= hit/1', 'io/fail "Unexpected empty match in selected counting pattern"'),
            21: block('if hit/2 <= hit/1', 'io/fail "Unexpected empty match in selected substitution pattern"'),
        }),
    'revcomp': main('revcomp', 41,
        rows={'D': '1', 'S': '2-4 7-10 12-13 15-16 18 23-26 32-33 41',
              'C': '19 21 34 37-39'},
        headers=(6, 11, 27, 28, 29, 30), packed={
            14: block('if none? found', 'io/fail "Unsupported revcomp sequence byte"'),
            17: block('if column = 60', 'append output 10', 'column: 0'),
            20: block('if column > 0', 'append output 10'),
            31: block('if not none? header', 'emit-record output header sequence'),
            35: block('(first line) = 59'),
            36: block('not none? header', 'append sequence line'),
            40: block('if not none? header', 'emit-record output header sequence'),
        }),
    'spectralnorm': main('spectralnorm', 41,
        rows={'D': '1', 'S': '2 5-7 11-13 15-16 19-20 22-23 25 29 31 33 35-36 38-39 41',
              'V': '18', 'C': '8 21 24 26 40'},
        headers=(4, 10, 14, 17, 37), packed={
            28: block('ata: func [input [block!]]', 'product (product input false) true'),
            30: block('if n = 0', 'io/fail "Spectralnorm size must be positive"'),
            32: block('loop n', 'append u 1.0'),
            34: block('loop 10', 'v: ata u', 'u: ata v'),
        }),
    'io': source(BASE + 'support/clbg_io.reb', 47,
        rows={'D': '1', 'S': '2 5 9 11 13 17 20 22 30-32 34 36 38 40 42 45',
              'C': '14 21 23 39 43 46-47'},
        headers=(4, 8, 16, 18, 29, 33, 35, 37), packed={
            6: block('fail: func [message [string!]]', 'do make error! message'),
            10: block('if any [none? arguments empty? arguments]', 'fail "Missing numeric workload size"'),
            12: block('if value < 0', 'fail "Negative workload size"'),
            19: block('if ((length? result) + (length? chunk)) > 2147483583', 'fail "Stdin exceeds signed byte series limit"'),
            24: block('write-output: func [data [binary!]]', 'commands/write-stdout data'),
            25: block('ascii: func [value [string!]]', 'to binary! value'),
            27: block('fixed: func [value [decimal!] digits [integer!]]', 'to string! commands/format-fixed value digits'),
            41: parts(('C', ']'), ('O', '['), ('C', ']')),
            44: block('if start <= length? data', 'append/only rows (copy at data start)'),
        }),
    'loader': source(BASE + 'support/clbg_primitives.reb', 12,
        rows={'D': '1', 'S': '2 4 6 12', 'C': '5 11'},
        headers=(3, (8, 9)), packed={
            7: block('unless module? extension', 'do make error! "General extension did not return a module"'),
            10: block('unless command? (get in extension name)', 'do make error! "Missing general extension command"'),
        }),
    'big': source(BASE + 'support/clbg_big.reb', 12,
        rows={'D': '1', 'S': '2 4', 'C': '12'}, headers=(3,), packed={
            5: block('from-int: func [value [integer!]]', 'to binary! form value'),
            6: block('to-int: func [value [binary!]]', 'to integer! to string! value'),
            7: block('add: func [a [binary!] b [binary!]]', 'commands/gmp-add a b'),
            8: block('subtract: func [a [binary!] b [binary!]]', 'commands/gmp-subtract a b'),
            9: block('multiply: func [a [binary!] b [binary!]]', 'commands/gmp-multiply a b'),
            10: block('floor-divide: func [a [binary!] b [binary!]]', 'commands/gmp-floor-divide a b'),
            11: block('compare: func [a [binary!] b [binary!]]', 'commands/gmp-compare a b'),
        }),
    'regex': source(BASE + 'support/clbg_regex.reb', 6,
        rows={'D': '1', 'S': '2 4', 'C': '6'}, headers=(3,), packed={
            5: block('find: func [pattern [binary!] subject [binary!] start [integer!]]',
                     'commands/pcre-find pattern subject start'),
        }),
    'extension': source(CORRECTED_C, 300,
        rows={
            'M': '1-6 40-41 85-90 122-123 189-190 219-220 230-231 267-268 272',
            'P': '7-18 42-43', 'D': '23-35',
            'S': '20 22 46-47 53-54 56-57 59 61-63 67-68 70 74 76-78 84 91 94-95 98-102 110-111 114-115 124-126 129 132-133 136-137 140-144 152-153 155 157-158 160 162-163 165-167 169-170 172-174 183-184 186-188 191 194-195 197-198 200 202-203 205 208 212 214 216 221 223-225 232-234 236 238 242 246-247 249-250 252 255 257 262-264 266 269-270 273-274 278 280-282 284 290',
            'C': '48 64 79 103 120 130 138 145 154 159 164 171 175 196 204 209 213 226 239 243 256 258 275 285 299-300',
        },
        headers=(45, (50, 51), 66, 81, 105, 112, 127, 135, 139, 146, 156, 161, 168,
                 177, 193, 201, 206, 210, 228, 235, 245, 251, 260, 277, 289, 293),
        raw_headers=(52, 72, (82, 83), (92, 93), 109, (180, 182), 185, 248, 261, 265),
        packed={
            37: parts(('H', 'enum'), ('O', '{'), ('E', 'CMD_ADD,'), ('E', 'CMD_SUBTRACT,'),
                      ('E', 'CMD_MULTIPLY,'), ('E', 'CMD_FLOOR_DIVIDE,'), ('E', 'CMD_COMPARE,')),
            38: parts(('E', 'CMD_FIND,'), ('E', 'CMD_READ,'), ('E', 'CMD_WRITE,'),
                      ('E', 'CMD_FORMAT'), ('C', '};')),
            55: c_if('if (!series || RL_SERIES(series, RXI_SER_WIDE) != 1)', 'return 0;'),
            58: c_if('if (index > tail || tail > BYTE_LIMIT)', 'return 0;'),
            60: c_if('if (!data && tail != 0)', 'return 0;'),
            69: c_if('if (!bytes_view(frame, argument, &bytes, &length) || length == 0)', 'return NULL;'),
            71: c_if('if (first == length)', 'return NULL;'),
            73: c_if("if (bytes[i] < '0' || bytes[i] > '9')", 'return NULL;'),
            75: c_if('if (!copy)', 'return NULL;'),
            96: c_if('if (!data)', 'return fail(frame, "Reserved byte result storage is invalid");'),
            97: c_if('if (length != 0)', 'memcpy(data, bytes, length);'),
            106: c_if('if (RXA_COUNT(frame) != 2)', 'return fail(frame, "Two decimal binary operands required");'),
            107: parts(('S', 'const unsigned char *a_bytes,'), ('S', '*b_bytes;')),
            108: parts(('S', 'size_t a_length,'), ('S', 'b_length;')),
            113: parts(('H', 'case CMD_ADD:'), ('H', 'case CMD_SUBTRACT:')),
            116: parts(('H', 'case CMD_MULTIPLY:'), ('S', 'capacity = a_length + b_length + 1U;'), ('S', 'break;')),
            117: parts(('H', 'case CMD_FLOOR_DIVIDE:'), ('S', 'capacity = a_length + 2U;'), ('S', 'break;')),
            118: parts(('H', 'case CMD_COMPARE:'), ('S', 'capacity = 0;'), ('S', 'break;')),
            119: parts(('H', 'default:'), ('S', 'return fail(frame, "Unknown arithmetic operation");')),
            121: c_if('if (capacity > BYTE_LIMIT)', 'return fail(frame, "Decimal result reserve exceeds signed series range");'),
            128: parts(('S', 'free(a_text);'), ('S', 'free(b_text);')),
            131: parts(('S', 'mpz_t a,'), ('S', 'b,'), ('S', 'result;')),
            134: parts(('S', 'free(a_text);'), ('S', 'free(b_text);')),
            147: parts(('H', 'case CMD_ADD:'), ('S', 'mpz_add(result, a, b);'), ('S', 'break;')),
            148: parts(('H', 'case CMD_SUBTRACT:'), ('S', 'mpz_sub(result, a, b);'), ('S', 'break;')),
            149: parts(('H', 'case CMD_MULTIPLY:'), ('S', 'mpz_mul(result, a, b);'), ('S', 'break;')),
            150: parts(('H', 'case CMD_FLOOR_DIVIDE:'), ('S', 'mpz_fdiv_q(result, a, b);'), ('S', 'break;')),
            151: parts(('H', 'default:')),
            178: parts(('S', 'const unsigned char *pattern,'), ('S', '*subject;')),
            179: parts(('S', 'size_t pattern_length,'), ('S', 'subject_length;')),
            192: c_if('if (!compile)', 'return fail(frame, "Unable to allocate PCRE2 compile context");'),
            199: c_if('if (!code)', 'return fail(frame, "PCRE2 pattern compilation failed");'),
            207: parts(('S', 'pcre2_match_data_free(match);'), ('S', 'pcre2_code_free(code);')),
            211: parts(('S', 'pcre2_match_data_free(match);'), ('S', 'pcre2_code_free(code);')),
            215: parts(('S', 'PCRE2_SIZE begin = positions[0],'), ('S', 'end = positions[1];')),
            217: parts(('S', 'pcre2_match_data_free(match);'), ('S', 'pcre2_code_free(code);')),
            218: c_if('if (!valid)', 'return fail(frame, "Invalid PCRE2 byte offsets");'),
            222: parts(('S', 'RXA_TYPE(frame, 1) ='), ('S', 'RXA_TYPE(frame, 2) = RXT_INTEGER;')),
            229: c_if('if (RXA_COUNT(frame) != 0)', 'return fail(frame, "Read-stdin-chunk takes no arguments");'),
            237: c_if('if (count < 0 && errno == EINTR)', 'continue;'),
            240: c_if('if (count < 0)', 'return fail(frame, "Stdin byte read failed");'),
            241: c_if('if (count == 0)', 'return RXR_NONE;'),
            253: c_if('if (count < 0 && errno == EINTR)', 'continue;'),
            254: c_if('if (count <= 0)', 'return fail(frame, "Stdout byte write failed");'),
            271: c_if('if (length < 0 || (size_t)length >= sizeof text)', 'return fail(frame, "Decimal formatting exceeded stack capacity");'),
            279: c_if('if (!library || !CHECK_STRUCT_ALIGN || sizeof(RXIARG) != 16 || sizeof(double) != 8)', 'return NULL;'),
            283: parts(('H', 'if (version[1] != 3 || version[2] != 22 || version[3] != 1)'),
                       ('O', '{'), ('S', 'RL = NULL;'), ('S', 'return NULL;'), ('C', '}')),
            287: parts(('H', 'RXIEXT int RX_Quit(int options)'), ('O', '{'),
                       ('S', '(void)options;'), ('S', 'RL = NULL;'), ('S', 'return 0;'), ('C', '}')),
            291: c_if('if (!RL || !frame)', 'return RXR_NO_COMMAND;'),
            292: c_if('if (command >= CMD_ADD && command <= CMD_COMPARE)', 'return arithmetic(command, frame);'),
            294: parts(('H', 'case CMD_FIND:'), ('S', 'return find_bytes(frame);')),
            295: parts(('H', 'case CMD_READ:'), ('S', 'return read_stdin(frame);')),
            296: parts(('H', 'case CMD_WRITE:'), ('S', 'return write_stdout(frame);')),
            297: parts(('H', 'case CMD_FORMAT:'), ('S', 'return format_fixed(frame);')),
            298: parts(('H', 'default:'), ('S', 'return RXR_NO_COMMAND;')),
        }),
}

WORKLOADS = ('binarytrees', 'fannkuchredux', 'fasta', 'knucleotide', 'mandelbrot',
             'nbody', 'pidigits', 'regexredux', 'revcomp', 'spectralnorm')
BUNDLES = {name: (name, 'io', 'loader', 'extension') +
           (('big',) if name == 'pidigits' else ('regex',) if name == 'regexredux' else ())
           for name in WORKLOADS}

# These descriptions are source-specific review evidence, not syntax rules.
DECISIONS = {
    'fannkuch-zero': 'Count the additive zero-size main instead of the archived rejecting main. Its row7 either is one composed binding; all positive-size permutation/flip statements remain unchanged. Loader row2 selects the exact retained IO facade.',
    'metadata': 'Rebol header/spec/type/local/argument blocks are structural data; preserve authored data wrapping.',
    'functions': 'Every exact func body here has explicit brackets: header1/open0/body owners/close1, even one-expression bodies.',
    'context': 'The three exact context constructors have evaluated definition bodies: header1/open0/body owners/close1.',
    'conditions': 'while condition blocks, including chunk/hit bindings, remain part of the single loop header; body block is separate.',
    'either': 'Only listed scalar-result compositions are single values. Multi-statement arms retain body owners and both written closes; no unwritten else header is invented.',
    'case': 'revcomp case and each written condition arm have explicit headers; the empty comment arm retains its written close.',
    'callback': 'knucleotide row61 combines sort/compare containing prefix with the first func header; one value body and one close follow.',
    'switch-value': 'knucleotide base-code has four single-constant arms; retained n-control.c REBNATIVE(switch) returns selected block result or R_NONE on no match.',
    'c-module': 'C rows22-35 retain declaration and every authored string/data row; rows27-35 expose all nine command declarations. No second count of runtime-produced module text.',
    'c-enum': 'Rows37-38 contain header1/open0, nine independent enum constants, written close1.',
    'c-bindings': 'Comma declarations and the RXA_TYPE chain have explicit separate owners; macro invocations are counted as authored, without expansion.',
    'data': 'FASTA probability wrapping, nbody argument/data wrapping and regex pattern/replacement rows remain physical data units, including written data delimiters.',
}
