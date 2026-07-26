#define _POSIX_C_SOURCE 200809L

#include "platform.h"

#include <errno.h>
#include <stdio.h>
#include <string.h>

#ifdef _WIN32
#include <direct.h>

static void win_error(char *error, size_t size, const char *operation) {
    DWORD code = GetLastError();
    snprintf(error, size, "%s failed (Windows error %lu)", operation,
             (unsigned long)code);
}

int tw_platform_mkdir(const char *path) {
    if (_mkdir(path) == 0 || errno == EEXIST) return 0;
    return -1;
}

int tw_platform_map(tw_mapping *m, const char *path, size_t size, int create,
                    char *error, size_t error_size) {
    DWORD disposition = create ? OPEN_ALWAYS : OPEN_EXISTING;
    LARGE_INTEGER requested;
    LARGE_INTEGER current;
    memset(m, 0, sizeof(*m));
    requested.QuadPart = (LONGLONG)size;
    m->file = CreateFileA(path, GENERIC_READ | GENERIC_WRITE,
                          FILE_SHARE_READ, NULL, disposition,
                          FILE_ATTRIBUTE_NORMAL, NULL);
    if (m->file == INVALID_HANDLE_VALUE) {
        win_error(error, error_size, "CreateFile");
        return -1;
    }
    if (!GetFileSizeEx(m->file, &current)) {
        win_error(error, error_size, "GetFileSizeEx");
        CloseHandle(m->file);
        return -1;
    }
    if (current.QuadPart < requested.QuadPart) {
        if (!SetFilePointerEx(m->file, requested, NULL, FILE_BEGIN) ||
            !SetEndOfFile(m->file)) {
            win_error(error, error_size, "SetEndOfFile");
            CloseHandle(m->file);
            return -1;
        }
    }
    m->mapping = CreateFileMappingA(m->file, NULL, PAGE_READWRITE,
                                    requested.HighPart, requested.LowPart, NULL);
    if (!m->mapping) {
        win_error(error, error_size, "CreateFileMapping");
        CloseHandle(m->file);
        return -1;
    }
    m->address = MapViewOfFile(m->mapping, FILE_MAP_ALL_ACCESS, 0, 0, size);
    if (!m->address) {
        win_error(error, error_size, "MapViewOfFile");
        CloseHandle(m->mapping);
        CloseHandle(m->file);
        return -1;
    }
    m->size = size;
    return 0;
}

int tw_platform_flush(tw_mapping *m, char *error, size_t error_size) {
    if (!FlushViewOfFile(m->address, m->size) || !FlushFileBuffers(m->file)) {
        win_error(error, error_size, "flush");
        return -1;
    }
    return 0;
}

void tw_platform_unmap(tw_mapping *m) {
    if (m->address) UnmapViewOfFile(m->address);
    if (m->mapping) CloseHandle(m->mapping);
    if (m->file && m->file != INVALID_HANDLE_VALUE) CloseHandle(m->file);
    memset(m, 0, sizeof(*m));
}

unsigned long long tw_platform_now_ns(void) {
    FILETIME ft;
    ULARGE_INTEGER ticks;
    GetSystemTimePreciseAsFileTime(&ft);
    ticks.LowPart = ft.dwLowDateTime;
    ticks.HighPart = ft.dwHighDateTime;
    return (ticks.QuadPart - 116444736000000000ULL) * 100ULL;
}

#else

#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

int tw_platform_mkdir(const char *path) {
    if (mkdir(path, 0755) == 0 || errno == EEXIST) return 0;
    return -1;
}

int tw_platform_map(tw_mapping *m, const char *path, size_t size, int create,
                    char *error, size_t error_size) {
    struct stat st;
    int flags = O_RDWR | (create ? O_CREAT : 0);
    memset(m, 0, sizeof(*m));
    m->fd = open(path, flags, 0644);
    if (m->fd < 0) {
        snprintf(error, error_size, "open %s: %s", path, strerror(errno));
        return -1;
    }
    if (fstat(m->fd, &st) != 0) {
        snprintf(error, error_size, "fstat %s: %s", path, strerror(errno));
        close(m->fd);
        return -1;
    }
    if ((size_t)st.st_size < size && ftruncate(m->fd, (off_t)size) != 0) {
        snprintf(error, error_size, "ftruncate %s: %s", path, strerror(errno));
        close(m->fd);
        return -1;
    }
    m->address = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_SHARED, m->fd, 0);
    if (m->address == MAP_FAILED) {
        m->address = NULL;
        snprintf(error, error_size, "mmap %s: %s", path, strerror(errno));
        close(m->fd);
        return -1;
    }
    m->size = size;
    return 0;
}

int tw_platform_flush(tw_mapping *m, char *error, size_t error_size) {
    if (msync(m->address, m->size, MS_SYNC) != 0) {
        snprintf(error, error_size, "msync: %s", strerror(errno));
        return -1;
    }
    return 0;
}

void tw_platform_unmap(tw_mapping *m) {
    if (m->address) munmap(m->address, m->size);
    if (m->fd >= 0) close(m->fd);
    memset(m, 0, sizeof(*m));
    m->fd = -1;
}

unsigned long long tw_platform_now_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    return (unsigned long long)ts.tv_sec * 1000000000ULL +
           (unsigned long long)ts.tv_nsec;
}
#endif
