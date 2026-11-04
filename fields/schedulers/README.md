# Schedulers - Overview

How a cluster scheduler decides who runs where, with Slurm as the working example.

## Contents

| File | Description |
|------|-------------|
| [intro](/fields/schedulers/intro.md) | What a scheduler does and why it matters |
| [slurm-job-script-tale](/fields/schedulers/slurm-job-script-tale.md) | The story of job.sh and the snapshot Slurm takes of it |
| [slurm-pam-adopt](/fields/schedulers/slurm-pam-adopt.md) | Closing the SSH backdoor with pam_slurm_adopt |
| [slurm-reboot-order](/fields/schedulers/slurm-reboot-order.md) | Rebooting a Slurm cluster without losing jobs |
| [slurm-mixed-gpus](/fields/schedulers/slurm-mixed-gpus/README.md) | Series: mixing H100s and A100s in one Slurm job, and when it pays off |
| [slurm-accounting-multi-tenancy](/fields/schedulers/slurm-accounting-multi-tenancy.md) | Who stores and who enforces multi-tenant rules: slurmdbd, associations, QOS, fairshare |
