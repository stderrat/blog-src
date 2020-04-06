#!/bin/bash

current_dir=$PWD
current_date=`date +%Y%M%d:%H%m`

echo "pulling latest changes"
git pull

echo "Pushing local changes"

git status
git add .
git commit -m "changes of $current_date"
git push -u origin master

cd public/

echo "Publish Blog"
cp -r * ../../stderrat.github.io
cd ../../stderrat.github.io
git status
git add .
git commit -m "changes of $current_date"
git push -u origin master

cd $current_dir
