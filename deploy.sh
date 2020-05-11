#!/bin/bash

echo "Do not use - Use circleCI instead"
exit

current_dir=$PWD
current_date=`date +%Y%M%d:%H%m`


echo "pulling latest changes"
git pull
cd ../stderrat.github.io
git pull
cd $current_dir

if ! [ -x "$(command -v node)" ]; then
  echo 'Error: nodejs not found, Consider installing it.' >&2
  echo "Skipping Search Index ... new posts will not be found"
else
  echo "Creating Search Index"
  node ./build-index.js
fi

sleep 5

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
