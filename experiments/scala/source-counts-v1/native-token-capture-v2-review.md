# Native parser correction validation

The revised reader compiled successfully and processed the same 80 retained
inputs in one supervised JVM. All 80 stock/observed parser transports match
exactly. All 72 positive inputs have complete coverage, including the ten
application sources. All eight negative fixtures remain rejected.

The [independent comparison](native-token-capture-v2-review.json) checks every
input against the original native capture. After accounting for the three newly
recorded native type/container markers and the corrected graph classification,
every original graph field is unchanged. All source bytes, token events,
physical intervals, native comments and whitespace intervals are unchanged.
The only removed coverage issue is the erroneous native-container graph issue.

The actual new records identify 41 `EmptyTree`, 22 `EmptyValDef` and 30 `Thicket`
nodes carrying the reference-identical native `NoType` marker. These observations
match the narrowly scoped [candidate correction](candidate-token-capture-v2/).
Parser errors, the terminal U+001A gap and the unsupported XML handoff retain
their original rejection evidence.

The [native report](native-token-capture-v2/report.json) records the two processes,
their complete artifacts and verified input closure. This establishes parser
transport and physical-coverage evidence for the retained inputs. Canonical
source ownership, LOC projection and benchmark required-work qualification
remain separate stages; this reader executes no benchmark main.
