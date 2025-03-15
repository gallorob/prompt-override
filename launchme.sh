#!/bin/bash

CONDA_ENV="prompt-override"
PYTHON_SCRIPT="./main.py"
GEOMETRY="94x35+0+0"

xfce4-terminal --geometry="$GEOMETRY" --initial-title="Prompt Override" --hide-menubar --hide-toolbar -e "bash -c 'source ~/anaconda3/etc/profile.d/conda.sh; conda activate \"$CONDA_ENV\"; python \"$PYTHON_SCRIPT\"'"
