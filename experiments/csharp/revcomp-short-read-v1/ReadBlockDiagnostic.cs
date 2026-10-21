// Untimed helper diagnostic only. Benchmark application source is not this file.
using System;
using System.Security.Cryptography;

public static partial class Program
{
    public static void ExerciseReadBlock()
    {
        foreach (int length in new[] { 0, 1, 17, 65537, BUFFER_SIZE, BUFFER_SIZE + 19 })
        foreach (int maximumRead in new[] { 3, 4093, 65536 })
        {
            byte[] payload = new byte[length];
            for (int i = 0; i < length; i++) payload[i] = (byte)(i * 37 + 17);
            int consumed = 0;
            int calls = 0;
            SpanFunc<byte> source = span =>
            {
                calls++;
                int take = Math.Min(span.Length, Math.Min(maximumRead, payload.Length - consumed));
                payload.AsSpan(consumed, take).CopyTo(span);
                consumed += take;
                return take;
            };
            byte[] block = new byte[BUFFER_SIZE];
            Array.Fill(block, (byte)0xA5);
            int actualLength = ReadBlock(source, block);
            int expectedLength = Math.Min(BUFFER_SIZE, payload.Length);
            bool prefix = actualLength == expectedLength &&
                block.AsSpan(0, expectedLength).SequenceEqual(payload.AsSpan(0, expectedLength));
            bool tail = true;
            for (int i = expectedLength; i < block.Length; i++) tail &= block[i] == 0;
            Console.WriteLine($"{length} {maximumRead} {actualLength} {consumed} {calls} {prefix} {tail} " +
                Convert.ToHexString(SHA256.HashData(block)));
            if (!prefix || !tail || consumed != expectedLength)
                throw new InvalidOperationException("Short-read prefix, length or cleared tail differs");
        }
    }
}

static class ReadBlockDiagnostic
{
    static void Main() => Program.ExerciseReadBlock();
}
