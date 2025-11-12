#!/usr/bin/env bash
# start_backend.sh — ensures env vars are set before Python loads anything

export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export OPENBLAS_VERBOSE=0
export OPENBLAS_MAIN_FREE=1
export OMP_WAIT_POLICY=passive
export XGBOOST_THREAD_POOL_SIZE=1
export TF_NUM_INTEROP_THREADS=1
export TF_NUM_INTRAOP_THREADS=1

# show effective env (for debugging)
echo "Effective BLAS env:"
echo "OMP_NUM_THREADS=$OMP_NUM_THREADS"
echo "OPENBLAS_NUM_THREADS=$OPENBLAS_NUM_THREADS"
echo "OPENBLAS_MAIN_FREE=$OPENBLAS_MAIN_FREE"
echo "OPENBLAS_VERBOSE=$OPENBLAS_VERBOSE"
echo "OMP_WAIT_POLICY=$OMP_WAIT_POLICY"

# replace the shell with the python process so imports see these env vars
exec python -W ignore -m backend.main