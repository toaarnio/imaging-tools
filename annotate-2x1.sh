#!/bin/bash

FILE=$1
SUFFIX=${FILE##*.}
BASENAME="$(basename --suffix .$SUFFIX $FILE)"
echo "Annotating ${FILE}, generating ${BASENAME}.jpg..."

convert ${FILE} -pointsize 200 -fill red -strokewidth 5 -stroke darkred \
        -gravity NorthWest -annotate +0-25 "Basic Pipe" \
        -gravity NorthEast -annotate +0-25 "Advanced Pipe" \
        ${BASENAME}.jpg
