#include <stdio.h>
#include <stdlib.h>
#include <omp.h>
#include <stdint.h>

// Define the structure for a log entry
typedef struct {
    double time; // Time in seconds
    uint64_t id;      // User-provided ID
    int32_t thread_id; // ID of the thread writing the timestamp
 } __attribute__((packed)) LogEntry;

// Global file pointer for the log file
FILE *logFile = NULL;

// Function to initialize the log system
int __timer_init__(const char *filename) {
    logFile = fopen(filename, "wb"); // Open the file in binary write mode
    if (!logFile) {
        perror("Error opening log file");
        return -1;
    }
    return 0;
}

// Function to capture the current time and save it along with the ID
int __timer_capture__(int id) {
    if (!logFile) {
        fprintf(stderr, "Log system not initialized.\n");
        return -1;
    }


    LogEntry entry;
    entry.time = omp_get_wtime(); // Capture the current time
    entry.id = id;
    entry.thread_id = omp_get_thread_num();

    // Write the log entry to the file
    if (fwrite(&entry, sizeof(LogEntry), 1, logFile) != 1) {
        perror("Error writing to log file");
        return -1;
    }
    return 0;
}

// Function to finalize the log system
void __timer_finish__() {
    if (logFile) {
        fclose(logFile);
        logFile = NULL;
    }
}

// int main() {
//     // Example usage of the log system
//     if (__timer_init__("time_logs.bin") != 0) {
//         return 1;
//     }

//     // Simulate logging with some IDs
//     for (int i = 0; i < 5; i++) {
//         if (__timer_capture__(i) != 0) {
//             fprintf(stderr, "Failed to log time for ID %d\n", i);
//         }
//     }

//     __timer_finish__();
//     return 0;
// }
