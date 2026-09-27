# System Administration - Linux - MPI

## Table of Contents
- [System Administration - Linux - MPI](#system-administration---linux---mpi)
  - [Table of Contents](#table-of-contents)


Verify that it creates 4 ranks and bind each rank to a specific core:
```bash
mpirun \
  --report-bindings \
  -np 4 \
  --bind-to core \
  --map-by ppr:1:numa \
  hostname
```

Expected output:
```bash
Rank 0 bound to core 0
Rank 1 bound to core 24
Rank 2 bound to core 48
Rank 3 bound to core 72
```

