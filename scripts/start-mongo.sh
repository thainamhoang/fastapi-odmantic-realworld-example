#!/bin/bash
docker run --rm -p 27017:27017 --name realworld-example -e "MONGODB_URI=mongodb+srv://thainamhoang:mTLgcHql2urHs8WX@cluster0.rtq8bpw.mongodb.net/test" -d mongo:latest

