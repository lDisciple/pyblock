#!/bin/bash
cd editor || exit
npm run build-engine || exit
cd ..
rm -rf static/editor
mkdir -p static/editor
mv editor/dist/* static/editor/
rm -d editor/dist
echo "Complete"