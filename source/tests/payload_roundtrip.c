#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>

#include "../src/payload_generated.h"

static int make_parent_directories(char *path) {
    for (char *cursor = path + 1; *cursor; cursor++) {
        if (*cursor != '/') continue;
        *cursor = 0;
        if (mkdir(path, 0755) != 0 && errno != EEXIST) return -1;
        *cursor = '/';
    }
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    for (size_t index = 0; index < g_payload_file_count; index++) {
        size_t length = strlen(argv[1]) + strlen(g_payload_files[index].path) + 2;
        char *destination = calloc(length, 1);
        if (!destination) return 3;
        snprintf(destination, length, "%s/%s", argv[1], g_payload_files[index].path);
        if (make_parent_directories(destination) != 0) return 4;
        FILE *file = fopen(destination, "wb");
        if (!file) return 5;
        if (fwrite(g_payload_files[index].data, 1, g_payload_files[index].size, file) != g_payload_files[index].size) return 6;
        fclose(file);
        free(destination);
    }
    printf("%zu payload files reconstructed\n", g_payload_file_count);
    return 0;
}
