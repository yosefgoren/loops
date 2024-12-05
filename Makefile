all: main.samples.json

CXX=g++
INCLUDES=-I./NPB-CPP/NPB-OMP\
	-I./NPB-CPP/NPB-OMP/BT\
	-I./NPB-CPP/NPB-OMP/CG\
	-I./NPB-CPP/NPB-OMP/common\
	-I./NPB-CPP/NPB-OMP/config\
	-I./NPB-CPP/NPB-OMP/EP\
	-I./NPB-CPP/NPB-OMP/FT\
	-I./NPB-CPP/NPB-OMP/IS\
	-I./NPB-CPP/NPB-OMP/LU\
	-I./NPB-CPP/NPB-OMP/MG\
	-I./NPB-CPP/NPB-OMP/SP\
	-I./NPB-CPP/NPB-OMP/sys

FLAGS=-fopenmp $(INCLUDES)

main.scopes.json: main.cpp scrape.py
	python3 scrape.py --input main.cpp --output $@

main.targets.json: main.scopes.json prune.py
	python3 prune.py --input main.scopes.json --output $@

main.timed.cpp: main.targets.json main.cpp modify.py
	python3 modify.py --read_file main.cpp --write_file $@ --logs_filename main.times --targets main.targets.json

main.timed.run: timer.hpp main.timed.cpp
	$(CXX) $(FLAGS) -o $@ main.timed.cpp

main.times: main.timed.run
	./main.timed.run

main.samples.json: main.times main.cpp main.targets.json collect.py
	python3 collect.py -o $@ --runtimes_file main.times --source_file main.cpp --loops_file main.targets.json

clean:
	rm -f main.scopes.json main.targets.json main.timed.cpp main.timed.run main.times main.samples.json