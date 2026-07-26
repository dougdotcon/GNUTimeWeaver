#include "demo_agent.h"
#include "timeweaver.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void usage(FILE *stream) {
    fputs("GNU TimeWeaver 0.1.0\n\n"
          "Usage:\n"
          "  timeweaver init <workspace>\n"
          "  timeweaver demo <workspace>\n"
          "  timeweaver branch <workspace> <node-id> <prompt>\n"
          "  timeweaver export <workspace>\n"
          "  timeweaver validate <workspace>\n", stream);
}

static int open_store(tw_store **store, const char *path, int create) {
    if (tw_open(store, path, create) != 0) {
        fprintf(stderr, "timeweaver: %s\n", tw_last_error(*store));
        tw_close(*store);
        *store = NULL;
        return -1;
    }
    return 0;
}

int main(int argc, char **argv) {
    tw_store *store = NULL;
    int result = EXIT_FAILURE;
    if (argc < 3) {
        usage(stderr);
        return EXIT_FAILURE;
    }
    if (strcmp(argv[1], "init") == 0) {
        if (open_store(&store, argv[2], 1) == 0) {
            printf("Initialized TimeWeaver workspace at %s\n", argv[2]);
            result = EXIT_SUCCESS;
        }
    } else if (strcmp(argv[1], "demo") == 0) {
        uint64_t failed = 0, success = 0;
        if (open_store(&store, argv[2], 1) == 0 &&
            tw_demo_seed(store, &failed, &success) == 0) {
            fprintf(stderr, "Demo captured failure at node %llu and resumed to node %llu.\n",
                    (unsigned long long)failed, (unsigned long long)success);
            result = tw_demo_export_json(store) == 0 ? EXIT_SUCCESS : EXIT_FAILURE;
        } else if (store) {
            fprintf(stderr, "timeweaver: demo requires an empty workspace\n");
        }
    } else if (strcmp(argv[1], "branch") == 0 && argc >= 5) {
        uint64_t source = strtoull(argv[3], NULL, 10);
        uint64_t forked = 0, final = 0;
        if (open_store(&store, argv[2], 0) == 0 &&
            tw_demo_branch(store, source, argv[4], &forked, &final) == 0) {
            fprintf(stderr, "Forked node %llu as %llu; continuation ended at %llu.\n",
                    (unsigned long long)source, (unsigned long long)forked,
                    (unsigned long long)final);
            result = tw_demo_export_json(store) == 0 ? EXIT_SUCCESS : EXIT_FAILURE;
        }
    } else if (strcmp(argv[1], "export") == 0) {
        if (open_store(&store, argv[2], 0) == 0) {
            result = tw_demo_export_json(store) == 0 ? EXIT_SUCCESS : EXIT_FAILURE;
        }
    } else if (strcmp(argv[1], "validate") == 0) {
        if (open_store(&store, argv[2], 0) == 0 && tw_validate(store) == 0) {
            puts("Workspace is structurally valid.");
            result = EXIT_SUCCESS;
        } else if (store) {
            fprintf(stderr, "timeweaver: workspace validation failed\n");
        }
    } else {
        usage(stderr);
    }
    tw_close(store);
    return result;
}
