#!/bin/bash

# Directory containing your image files
image_dir="./images/ade20k/"

# Base output directory for attention maps
base_output_dir="attnmaps/large"

# Layer ID and other parameters
layer_id=1

# Iterate over each image in the directory
for image in "$image_dir"/*; do
    # Extract the base name of the image file (e.g., without path)
    image_name=$(basename "$image")

    # Remove the file extension from the base name
    image_basename="${image_name%.*}"

    # Define the specific output directory for this image
    output_dir="${base_output_dir}/${image_basename}"

    # Create the output directory if it doesn't exist
    mkdir -p "$output_dir"

    # Run the Python script
    python -m segm.scripts.show_attn_map \
        checkpoints/seg-l-mask-16/checkpoint.pth \
        "$image_dir/$image_name" \
        "$output_dir" \
        --layer-id "$layer_id" --dec --cls --cpu
done
