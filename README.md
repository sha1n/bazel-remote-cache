# Bazel Wrapper
This repository implements POC for a [Bazel](https://github.com/bazelbuild) wrapper script that automatically sets 
remote HTTP cache flags based on local environment fingerprint. 

## Why Use Remote Cache?
Building large projects can take a lot of time, even with Bazel. Remote caching with Bazel, allows any build machine to
reuse targets that have already been built by other (or the same) build machines and reduce build time significantly. 
That is true especially in projects that share a lot of common in-house frameworks and libraries as sources. 
However, in order to be able to share a cache, the binaries that are uploaded to the cache must be compatible with all 
the build machines that can potentially consume them and unfortunately, that might not be the case if you are using 
incompatible environments to build those targets. The term "Incompatible environments" refers to any component on the 
build environment that might have an effect on the built targets and that depends on your shell environment, installed 
OS packages, programming language tools and what not.    
    
This POC demonstrates an approach that gives correctness a top priority at the price of cache misses and storage space. 
It does so by segregating build environments' cache area based on a fingerprint that is based on MacOS version and Clang 
version and is calculated in real time (every time a Bazel command is executed). The finger print calculation 
demonstrated here is just an example and of course it can easily be changed/extended to more variables, as long as it 
doesn't have a significant performance impact.

### Other considerable approaches:
1. Have all build and development machines fully managed and aligned with the same OS and tools
2. Run all build on remote managed environments

## How To Use
1. Make sure you have Python 3 in your `PATH`
1. Copy `bazel`, `bazelwrapper.py` and `remotecache.py` into your `<REPO_HOME>/tools` directory
1. That's it! Bazel will execute the `bazel` script every time you run a Bazel command.