/* Untimed macOS fixture interposer, never a benchmark dependency.
 * Uses the SDK's official DYLD_INTERPOSE macro rather than a copied ABI.
 * Activation is explicit real stdout: "MECH-IO-FAULT-V1" including its NUL.
 * Reads/writes outside standard input/output, and all calls before that marker,
 * pass through unchanged. No workload algorithm is implemented here.
 */
#include <errno.h>
#include <fcntl.h>
#include <mach-o/dyld-interposing.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static atomic_int armed;
static atomic_ullong read_calls, write_calls, read_eintr, write_eintr;
static atomic_ullong read_short, write_short, read_bytes, write_bytes;
static const unsigned char marker[] = "MECH-IO-FAULT-V1";

/* The official dyld example calls the original function from its replacement;
 * references originating in this interposer image are not redirected to itself.
 * This behavior still requires an actual activation/counter receipt.
 */
static ssize_t fixture_read(int fd, void *buffer, size_t count) {
    if (fd != STDIN_FILENO || !atomic_load(&armed)) return read(fd, buffer, count);
    unsigned long long call = atomic_fetch_add(&read_calls, 1);
    if (call < 2) {
        atomic_fetch_add(&read_eintr, 1);
        errno = EINTR;
        return -1;
    }
    size_t limit = count < 7 ? count : 7;
    ssize_t result = read(fd, buffer, limit);
    int saved_errno = errno;
    if (result > 0) {
        atomic_fetch_add(&read_bytes, (unsigned long long)result);
        if ((size_t)result < count) atomic_fetch_add(&read_short, 1);
    }
    errno = saved_errno;
    return result;
}

static ssize_t fixture_write(int fd, const void *buffer, size_t count) {
    if (fd == STDOUT_FILENO && !atomic_load(&armed)
        && count == sizeof marker && memcmp(buffer, marker, sizeof marker) == 0) {
        atomic_store(&armed, 1);
    }
    if (fd != STDOUT_FILENO || !atomic_load(&armed)) return write(fd, buffer, count);
    unsigned long long call = atomic_fetch_add(&write_calls, 1);
    if (call < 2) {
        atomic_fetch_add(&write_eintr, 1);
        errno = EINTR;
        return -1;
    }
    size_t limit = count < 11 ? count : 11;
    ssize_t result = write(fd, buffer, limit);
    int saved_errno = errno;
    if (result > 0) {
        atomic_fetch_add(&write_bytes, (unsigned long long)result);
        if ((size_t)result < count) atomic_fetch_add(&write_short, 1);
    }
    errno = saved_errno;
    return result;
}

DYLD_INTERPOSE(fixture_read, read)
DYLD_INTERPOSE(fixture_write, write)

__attribute__((destructor)) static void fixture_report(void) {
    const char *path = getenv("MECH_REBOL_IO_FAULT_REPORT");
    if (!path || path[0] != '/') _exit(90);
    int fd = open(path, O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW | O_CLOEXEC, 0600);
    if (fd < 0) _exit(90);
    char record[768];
    int length = snprintf(record, sizeof record,
        "{\"schema\":\"rebol-primitive-io-fault-observation-v1\","
        "\"armed\":%d,\"read_calls\":%llu,\"write_calls\":%llu,"
        "\"read_eintr\":%llu,\"write_eintr\":%llu,"
        "\"read_short\":%llu,\"write_short\":%llu,"
        "\"read_bytes\":%llu,\"write_bytes\":%llu}\n",
        atomic_load(&armed), atomic_load(&read_calls), atomic_load(&write_calls),
        atomic_load(&read_eintr), atomic_load(&write_eintr),
        atomic_load(&read_short), atomic_load(&write_short),
        atomic_load(&read_bytes), atomic_load(&write_bytes));
    if (length < 0 || (size_t)length >= sizeof record) _exit(90);
    size_t done = 0;
    while (done < (size_t)length) {
        ssize_t count = write(fd, record + done, (size_t)length - done);
        if (count < 0 && errno == EINTR) continue;
        if (count <= 0) _exit(90);
        done += (size_t)count;
    }
    if (close(fd) != 0) _exit(90);
}
