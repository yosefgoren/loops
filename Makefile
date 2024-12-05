all: print

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

scopes.json: main.cpp scrape.py
	python3 scrape.py

targets.json: scopes.json prune.py
	python3 prune.py

main.timed.cpp: targets.json main.cpp modify.py
	python3 modify.py

timed_main: timer.hpp main.timed.cpp
	$(CXX) $(FLAGS) -o $@ main.timed.cpp

main.times: timed_main
	./timed_main

print: main.times parse_log.py
	python3 parse_log.py main.times

clean:
	rm -f scopes.json targets.json main.timed.cpp timed_main main.times