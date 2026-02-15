#!/bin/bash

# Get all image:tag combinations
docker images --format "{{.Repository}}:{{.Tag}}" | while read -r image; do
    # Skip if image is empty
    [[ -z "$image" ]] && continue
    
    # Keep kindest images
    if [[ "$image" == kindest/* ]]; then
        echo "Keeping: $image"
        continue
    fi
    
    # Keep 0.1.0 version
    if [[ "$image" == *:0.1.0 ]]; then
        echo "Keeping: $image"
        continue
    fi
    
    # Delete everything else
    echo "Deleting: $image"
    docker rmi "$image"
done
