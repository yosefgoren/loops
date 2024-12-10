all: main.samples.json

BASEDIR=./NPB-CPP/NPB-OMP
# TARGET_NAME=bt
TARGET_SRC=$(BASEDIR)/BT/bt.cpp
SRC_COPY=$(BASEDIR)/BT/orig_bt.cpp
BIN_DIR=$(BASEDIR)/bin
TARGET_EXEC=bt.S
LABELS=modified.label

# TARGET_SRC is never a dependency since it is modified (and will cause incorrect reconstruction)
$(SRC_COPY):
	cp $(TARGET_SRC) $@

main.scopes.json: scrape.py
	python3 scrape.py --input $(TARGET_SRC) -o $@

main.targets.json: main.scopes.json prune.py
	python3 prune.py --input main.scopes.json -o $@

modified.label: main.targets.json modify.py $(SRC_COPY)
	python3 modify.py --read_file $(TARGET_SRC) --write_file $(TARGET_SRC) --logs_filename main.times --targets main.targets.json
	touch $@

$(BASEDIR)/common/timer.hpp: timer.hpp
	cp $^ $@

$(TARGET_EXEC): modified.label $(BASEDIR)/common/timer.hpp
	$(MAKE) -C $(BASEDIR) bt

main.times: $(TARGET_EXEC)
	$(BIN_DIR)/$(TARGET_EXEC)

main.samples.json: main.times main.targets.json collect.py $(SRC_COPY)
	python3 collect.py -o $@ --runtimes_file main.times --source_file $(SRC_COPY) --loops_file main.targets.json

clean:
	rm -f main.scopes.json main.targets.json main.times main.samples.json $(LABELS)