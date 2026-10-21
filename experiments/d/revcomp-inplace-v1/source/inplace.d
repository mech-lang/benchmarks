// Buffered lookup-table adaptation of the retained D reverse-complement source.
import std;

void main() {
    ubyte[256] complement;
    foreach (i; 0 .. 256)
        complement[i] = cast(ubyte)i;
    foreach (i, c; "ACBDGHKMNSRUTWVYacbdghkmnsrutwvy")
        complement[cast(ubyte)c] = "TGVHCDMKNSYAAWBRTGVHCDMKNSYAAWBR"[i];
    auto input = cast(ubyte[])stdin.byChunk(1 << 20).join;
    ubyte[1 << 20] buffer;
    size_t used;
    void emit(scope const(ubyte)[] bytes) {
        while (bytes.length) {
            auto take = min(bytes.length, buffer.length - used);
            buffer[used .. used + take] = bytes[0 .. take];
            used += take;
            bytes = bytes[take .. $];
            if (used == buffer.length) {
                stdout.rawWrite(buffer[]);
                used = 0;
            }
        }
    }
    size_t sequenceStart, sequenceEnd;
    bool haveHeader;
    void finish() {
        if (!haveHeader)
            return;
        auto bases = input[sequenceStart .. sequenceEnd];
        size_t left, right = bases.length;
        while (left < right) {
            --right;
            auto first = complement[bases[left]];
            auto last = complement[bases[right]];
            bases[left++] = last;
            bases[right] = first;
        }
        for (size_t offset; offset < bases.length; offset += 60) {
            emit(bases[offset .. min(offset + 60, bases.length)]);
            emit(cast(const(ubyte)[])"\n");
        }
    }
    size_t cursor;
    while (cursor < input.length) {
        auto start = cursor;
        while (cursor < input.length && input[cursor] != '\r' && input[cursor] != '\n')
            ++cursor;
        auto end = cursor;
        if (cursor < input.length && input[cursor] == '\r')
            ++cursor;
        if (cursor < input.length && input[cursor] == '\n')
            ++cursor;
        if (start != end && input[start] == '>') {
            finish();
            emit(input[start .. end]);
            emit(cast(const(ubyte)[])"\n");
            haveHeader = true;
            sequenceStart = sequenceEnd = cursor;
        } else if (haveHeader && (start == end || input[start] != ';')) {
            foreach (index; start .. end)
                input[sequenceEnd++] = input[index];
        }
    }
    finish();
    if (used)
        stdout.rawWrite(buffer[0 .. used]);
}
