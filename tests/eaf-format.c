/* Read the candidate files through AirBoat's actual portable decoder. */
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include "eaf_decoder.h"

int main(int argc, char **argv)
{
    assert(argc > 1);
    size_t frames = 0;
    for (int i = 1; i < argc; ++i) {
        FILE *file = fopen(argv[i], "rb");
        assert(file != NULL);
        assert(fseek(file, 0L, SEEK_END) == 0);
        long size = ftell(file);
        assert(size > 0 && fseek(file, 0L, SEEK_SET) == 0);
        unsigned char *bytes = malloc((size_t)size);
        assert(bytes != NULL && fread(bytes, 1U, (size_t)size, file) == (size_t)size);
        assert(fclose(file) == 0);
        eaf_decoder_handle_t decoder = eaf_decoder_create(360U * 360U);
        eaf_info_t info;
        eaf_frame_t frame;
        assert(decoder != NULL && eaf_decoder_open(decoder, bytes, (size_t)size));
        assert(eaf_decoder_info(decoder, &info) && info.width == 240U && info.height == 240U);
        for (unsigned n = 0; n < info.frames; ++n) {
            assert(eaf_decoder_frame(decoder, (uint16_t)n, &frame));
            assert(frame.width == 240U && frame.height == 240U);
            ++frames;
        }
        eaf_decoder_destroy(decoder);
        free(bytes);
    }
    printf("{\"status\":\"passed\",\"assets\":%d,\"frames\":%zu}\n", argc-1, frames);
    return 0;
}
