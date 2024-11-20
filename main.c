#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <sys/time.h>

int w = 80;

typedef enum {
    READING_WORD,
    READING_SPACE
} ReadingState;

typedef struct {
    long * ws_starts;
    long word_count;
} WordSpaceData;

typedef struct {
    long * lines;
    long line_count;
} LineData;


int is_word_char(char c) {
    return (c >= '!') && (c <= '~');
}


WordSpaceData word_starts(char * text_start, long file_size) {
    // first pass: count the words
    ReadingState state = READING_SPACE;
    int word_count = 0;
    for (char * pos = text_start; pos < text_start + file_size; pos++) {
        if (state == READING_SPACE && is_word_char(*pos)) {
            word_count++;
            state = READING_WORD;
        } else if (state == READING_WORD && ! is_word_char(*pos)) {
            state = READING_SPACE;
        } else { }
    }

    // second pass: fill the ws_starts array
    long * ws_starts = (long *)malloc(2 * word_count * sizeof(long));
    if (ws_starts == NULL) {
        perror("Error allocating memory for word_starts");
        return (WordSpaceData) {NULL, 0};
    }

    ws_starts[2 * word_count - 1] = file_size; 

    word_count = 0;
    state = READING_SPACE;
    for (char * pos = text_start; pos < text_start + file_size; pos++) {
        if (state == READING_SPACE && is_word_char(*pos)) {
            ws_starts[2 * word_count] = pos - text_start;
            state = READING_WORD;
        } else if (state == READING_WORD && ! is_word_char(*pos)) {
            ws_starts[2 * word_count + 1] = pos - text_start;
            state = READING_SPACE;
            word_count++;
        } else { }
    }

    return (WordSpaceData) {ws_starts, word_count};
}


bool compute_offsets(long * ws_starts, long word_count, long * offsets) {
    long cml_offset = 0;
    bool overlong_word = false;

    for (long i = 0; i < word_count; i++) {
        offsets[i] = cml_offset;

        long start = ws_starts[2 * i];
        long end = ws_starts[2 * i + 1];
        cml_offset += end - start;
        if (end - start > w) {
            overlong_word = true;
        }
    }
    
    offsets[word_count] = cml_offset;
    return overlong_word;
}


LineData line_break(long * offsets, long word_count) {
    long max_cost = 0;
    long * minima = (long *)malloc((word_count + 1) * sizeof(long));
    long * breaks = (long *)malloc((word_count + 1) * sizeof(long));

    for (long i = 0; i <= word_count; i++) {
        minima[i] = 1048576;
        breaks[i] = 0;
    }

    minima[0] = 0;
    breaks[0] = -1;


    for (long i = 0; i < word_count; i++) {
        for (long j = i + 1; j <= word_count; j++) {
            long width = offsets[j] - offsets[i] + j - i - 1;
            if (width > w) {
                if (j == i + 1) {
                    minima[j] = 0;
                    breaks[j] = i;
                }
                break;
            } else {
                long penalty = w - width;
                long long cost = minima[i] + penalty * penalty;
                if (cost > max_cost) {
                    max_cost = cost;
                }
                if (cost < minima[j]) {
                    minima[j] = cost;
                    breaks[j] = i;
                }
            }
        }
    }

    printf("Max cost: %lld\n", max_cost);

    // first pass: count the lines
    long line_count = 0;
    long j = word_count;
    while (j > 0) {
        j = breaks[j];
        line_count += 1;
    }

    // second pass: fill the lines array
    long * lines = (long *)malloc(line_count * sizeof(long));
    if (lines == NULL) {
        perror("Error allocating memory for lines");
        return (LineData) {NULL, 0};
    }

    j = word_count;
    long line = line_count - 1;
    while (j > 0) {
        lines[line] = j;
        j = breaks[j];
        line -= 1;
    }

    free(minima);
    free(breaks);

    return (LineData) {lines, line_count};
}


void print_lines(char * buffer, long * ws_starts, long * lines, long line_count) {
    ReadingState state;

    for (long i = 0; i < line_count; i++) {
        long line_start = (i == 0) ? 0 : ws_starts[2 * lines[i - 1]];
        long line_end = ws_starts[2 * lines[i] - 1];

        state = READING_SPACE;
        for (long j = line_start; j < line_end; j++) {
            if (is_word_char(buffer[j])) {
                printf("%c", buffer[j]);
                state = READING_WORD;
            } else {
                if (state == READING_WORD) {
                    printf(" ");
                }
                state = READING_SPACE;
            }
        }
        printf("\n");
    }
}


int main(int argc, char *argv[]) {
    struct timeval start, end;
    bool use_gpu = false;
    WordSpaceData ws_data;
    LineData l_data;
    long * offsets;

    if (argc < 4) {
        fprintf(stderr, "Usage: %s <filename> <line_width> <use_gpu>\n", "party");
        return 1;
    }

    w = atoi(argv[2]);
    use_gpu = atoi(argv[3]);
    
    // open text file
    FILE *file = fopen(argv[1], "r");
    if (file == NULL) {
        perror("Error opening file");
        return 1;
    }

    // copy file content to buffer
    fseek(file, 0, SEEK_END);
    long file_size = ftell(file);
    fseek(file, 0, SEEK_SET);

    char *buffer = (char *)malloc(file_size + 1);
    if (buffer == NULL) {
        perror("Error allocating memory");
        fclose(file);
        return 1;
    }

    fread(buffer, 1, file_size, file);
    buffer[file_size] = '\0';
    fclose(file);


    gettimeofday(&start, NULL);
    if (use_gpu) {
        // call GPU function
    } else {
        // find word starts
        ws_data = word_starts(buffer, file_size);
        if (ws_data.ws_starts == NULL) {
            free(buffer);
            return 1;
        }

        // find word offsets
        offsets = (long *)malloc((ws_data.word_count + 1) * sizeof(long)); 
        bool overlong_word = compute_offsets(ws_data.ws_starts, ws_data.word_count, offsets);

        // find line breaks
        l_data = line_break(offsets, ws_data.word_count);
        if (l_data.lines == NULL) {
            free(offsets);
            free(ws_data.ws_starts);
            free(buffer);
            return 1;
        }
    }

    gettimeofday(&end, NULL);

    //print_lines(buffer, ws_data.ws_starts, l_data.lines, l_data.line_count);

    double elapsed = (end.tv_sec - start.tv_sec) + (end.tv_usec - start.tv_usec) / 1000000.0;
    printf("\nElapsed time: %.6f seconds\n", elapsed);

    free(l_data.lines);
    free(offsets);
    free(ws_data.ws_starts);
    free(buffer);
    return 0;
}