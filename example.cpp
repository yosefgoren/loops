#include <stdio.h>
#include <omp.h>

int main(){
	//@#$init
	for(int i = 0; i < 4; ++i) {
		// printf("things\n");
	}
	for(int j = 0; j < 15; ++j) {
		for(int x = 0; x < 15; ++x) {
			// printf("stuff\b");
		}
	}
	//@#$finish
}