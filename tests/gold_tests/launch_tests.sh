#!/bin/bash
pushd $(dirname $0)
python ../gtest/gtest.py 
popd
