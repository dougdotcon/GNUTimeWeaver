CC ?= cc
CFLAGS ?= -O2 -std=c11 -Wall -Wextra -Wpedantic
CPPFLAGS := -Iinclude -Isrc/native
BUILD := build
CORE := src/native/platform.c src/native/store.c

.PHONY: all test clean vllm-image vllm-campaign

all: $(BUILD)/timeweaver

$(BUILD):
	mkdir -p $(BUILD)

$(BUILD)/timeweaver: $(CORE) src/native/demo_agent.c src/native/cli.c | $(BUILD)
	$(CC) $(CFLAGS) $(CPPFLAGS) $^ -o $@

$(BUILD)/timeweaver_tests: $(CORE) test/native_test.c | $(BUILD)
	$(CC) $(CFLAGS) $(CPPFLAGS) $^ -o $@

test: $(BUILD)/timeweaver_tests
	./$(BUILD)/timeweaver_tests

clean:
	rm -rf $(BUILD)

vllm-image:
	docker compose -f docker-compose.vllm.yml build

vllm-campaign:
	mkdir -p campaign-results
	docker compose -f docker-compose.vllm.yml run --rm campaign-runner
