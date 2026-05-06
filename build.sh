#!/bin/bash
echo "Installing dependencies..."
pip install -r requirements.txt

echo "Training lead scoring model..."
python scripts/train_model.py

echo "Build complete."
