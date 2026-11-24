#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

struct encoded {
    uint8_t *data;
    size_t length;
    size_t capacity;
};

extern int deploy_encode(const uint8_t *, size_t, struct encoded *);
extern void deploy_release(struct encoded *);

static uint64_t now_ns(void) {
    struct timespec timestamp;
    if (clock_gettime(CLOCK_MONOTONIC_RAW, &timestamp) != 0) {
        exit(3);
    }
    return (uint64_t)timestamp.tv_sec * UINT64_C(1000000000) + (uint64_t)timestamp.tv_nsec;
}

static int encode(const uint8_t *input, size_t length, int emit_stream) {
    struct encoded output = {0};
    uint64_t start = now_ns();
    int status = deploy_encode(input, length, &output);
    uint64_t elapsed = now_ns() - start;
    if (status != 0 || !output.data || !output.length || output.length > output.capacity) {
        fprintf(stderr, "encoder failed with status %d\n", status);
        if (status == 0) {
            deploy_release(&output);
        }
        return 4;
    }
    int failed = 0;
    if (emit_stream) {
        failed = fwrite(output.data, 1, output.length, stdout) != output.length;
    } else {
        failed = printf("%" PRIu64 "\t%zu\n", elapsed, output.length) < 0;
    }
    deploy_release(&output);
    return failed || fflush(stdout) != 0 ? 5 : 0;
}

int main(int argc, char **argv) {
    const int emit_stream = argc == 3 && strcmp(argv[2], "--verify") == 0;
    if (argc != 2 && !emit_stream) {
        return 1;
    }
    FILE *file = fopen(argv[1], "rb");
    if (!file || fseek(file, 0, SEEK_END) != 0) {
        return 2;
    }
    long size = ftell(file);
    if (size <= 0 || fseek(file, 0, SEEK_SET) != 0) {
        return 2;
    }
    size_t length = (size_t)size;
    uint8_t *input = malloc(length);
    if (!input || fread(input, 1, length, file) != length || fclose(file) != 0) {
        return 2;
    }
    int status = 0;
    if (emit_stream) {
        status = encode(input, length, 1);
    } else {
        if (puts("READY") < 0 || fflush(stdout) != 0) {
            return 5;
        }
        int command;
        while ((command = getchar()) == 'N') {
            status = encode(input, length, 0);
            if (status != 0) {
                break;
            }
        }
        if (!status && command != 'Q') {
            status = 6;
        }
    }
    free(input);
    return status;
}
