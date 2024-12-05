#include <stdio.h>
#include <unistd.h>

#define MICROSEC_IN_SEC (1000000)

int main(){
	//@#$init
	for(int i = 0; i < 4; ++i) {
		usleep(MICROSEC_IN_SEC*0.2);
	}
	for(int j = 0; j < 10; ++j) {
		for(int x = 0; x < 5; ++x) {
			usleep(MICROSEC_IN_SEC*0.02);
		}
	}
	//@#$finish
}