#!/bin/bash

# ==============================================================================
# THIRUPPAVAI 30-DAY PLANETARIUM ANIMATION STITCHER
# ==============================================================================

# Target configuration paths
INPUT_DIR="thiruppavai_sky_sequence"
OUTPUT_FILE="thiruppavai_862ad_sky_canopy.mp4"

# Check if the folder containing the generated PNG images exists
if [ ! -d "$INPUT_DIR" ]; then
    echo "Error: Directory '$INPUT_DIR' not found."
    echo "Please run your Python animation script first to generate the sky sheets."
    exit 1
fi

echo "======================================================================"
echo " Launching Video Processing Pipeline via FFmpeg Engine"
echo "======================================================================"

# Run FFmpeg compilation command:
# -r 1          : Set frame rate to 1 frame per second (1 day = 1 second on screen)
# -i            : Read sequential files with pattern 'day_XX_thiruppavai.png'
# -vcodec libx264 : Compress using the standard H.264 video codec
# -pix_fmt yuv420p: Format pixel coordinates safely for all video players
# -y            : Auto-overwrite the output file if it already exists
ffmpeg -r 1 \
       -i "$INPUT_DIR/day_%02d_thiruppavai.png" \
       -vcodec libx264 \
       -crf 18 \
       -pix_fmt yuv420p \
       -y "$OUTPUT_FILE"

# Verify successful compilation tracking
if [ $? -eq 0 ]; then
    echo "----------------------------------------------------------------------"
    echo " Success! Video animation file generated flawlessly."
    echo " Final Asset Link Location: ./$OUTPUT_FILE"
    echo "======================================================================"
else
    echo "Error: FFmpeg execution process hit an interruption."
    echo "Verify that 'ffmpeg' is installed and available in your system path."
fi

