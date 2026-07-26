#ifndef TIMEWEAVER_PLATFORM_H
#define TIMEWEAVER_PLATFORM_H

#include <stddef.h>

#ifdef _WIN32
#include <windows.h>
typedef struct tw_mapping {
    HANDLE file;
    HANDLE mapping;
    void *address;
    size_t size;
} tw_mapping;
#else
typedef struct tw_mapping {
    int fd;
    void *address;
    size_t size;
} tw_mapping;
#endif

int tw_platform_mkdir(const char *path);
int tw_platform_map(tw_mapping *mapping, const char *path, size_t size,
                    int create, char *error, size_t error_size);
int tw_platform_flush(tw_mapping *mapping, char *error, size_t error_size);
void tw_platform_unmap(tw_mapping *mapping);
unsigned long long tw_platform_now_ns(void);

#endif
