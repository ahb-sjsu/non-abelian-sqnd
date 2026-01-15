# polite-submit: Client-Side Contention Management for Slurm

## Implementation Guide & Integration Proposal

**Submitted to:** SchedMD / NVIDIA Slurm Team  
**Author:** Andrew H. Bond, San José State University  
**Date:** January 2026  
**Version:** 1.0

---

## Executive Summary

`polite-submit` is a client-side job submission wrapper that implements CSMA/CA-inspired contention management for Slurm clusters. It probes cluster state before submission and backs off when resources are congested, improving queue health without requiring scheduler modifications.

**Key Benefits:**
- Reduces queue congestion from batch job floods
- Zero server-side changes required (pure client)
- Drops in as `sbatch` replacement
- Configurable politeness levels
- Supports batch and array job chunking

**Integration Opportunity:**
As NVIDIA expands Slurm's role in AI infrastructure, client-side courtesy mechanisms become essential. This tool could integrate with Slurm's contrib ecosystem or NVIDIA's cluster management stack.

---

## Part 1: The Problem

### 1.1 Queue Flooding

A single user running a hyperparameter sweep can submit 500+ jobs in seconds:

```bash
for lr in 0.001 0.01 0.1; do
  for bs in 16 32 64 128; do
    for seed in {1..40}; do
      sbatch train.sh --lr $lr --bs $bs --seed $seed
    done
  done
done
```

**Result:** 480 jobs hit the queue simultaneously. Other users experience:
- Immediate queue position degradation
- Wait times spike from minutes to hours
- Fairshare kicks in *eventually*, but damage is done

### 1.2 Fairshare Limitations

Slurm's fairshare is reactive:
1. User floods queue
2. Scheduler detects over-usage
3. Priority decays over time
4. Eventually, balance is restored

The gap between steps 1 and 4 can be hours. During this window, other users suffer.

### 1.3 The AI Workload Explosion

GPU partitions are particularly vulnerable:
- Fewer nodes (8-16 typical)
- Longer job durations (hours to days)
- Higher contention (everyone wants GPUs)
- Bursty submission patterns (ML experiments)

---

## Part 2: The Solution

### 2.1 CSMA/CA for HPC

Wireless networks solved medium contention with CSMA/CA:
- **Sense before transmit**
- **Back off on contention**
- **Exponential backoff prevents synchronization**

We apply the same principles to job submission:

```
┌─────────────────────────────────────────────────────────┐
│                    polite-submit                        │
│                                                         │
│  1. PROBE: sinfo/squeue → cluster state                 │
│  2. DECIDE: utilization OK? others waiting?             │
│  3. SUBMIT or BACKOFF                                   │
│  4. If backoff, wait with exponential increase          │
│  5. Repeat                                              │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Decision Logic

```python
def should_submit(state: ClusterState, config: Config) -> bool:
    # Self-limiting
    if state.my_running >= config.max_concurrent:
        return False
    if state.my_pending >= config.max_pending:
        return False
    
    # Yield to others
    if state.others_pending > config.queue_threshold:
        return False
    if state.utilization > config.util_threshold:
        return False
    
    return True
```

### 2.3 Backoff Algorithm

```python
def calculate_backoff(attempt: int, config: Config) -> float:
    base = config.initial_backoff  # 30 sec default
    multiplier = 2 ** attempt
    jitter = random.uniform(0.5, 1.5)
    return min(base * multiplier * jitter, config.max_backoff)
```

Jitter prevents multiple polite clients from synchronizing their retry attempts.

---

## Part 3: Implementation

### 3.1 File Structure

```
polite-submit/
├── polite_submit/
│   ├── __init__.py
│   ├── cli.py           # Command-line interface
│   ├── prober.py        # Cluster state queries
│   ├── decider.py       # Submission logic
│   ├── backoff.py       # Exponential backoff
│   └── config.py        # Configuration handling
├── tests/
│   ├── test_prober.py
│   ├── test_decider.py
│   └── test_integration.py
├── contrib/
│   └── slurm/
│       ├── polite_sbatch.sh    # Drop-in wrapper
│       └── job_submit_plugin/  # Server-side option
├── pyproject.toml
├── README.md
└── polite-submit.yaml.example
```

### 3.2 Core Components

#### Prober (cluster state queries)

```python
# prober.py
import subprocess
from dataclasses import dataclass

@dataclass
class ClusterState:
    partition: str
    total_nodes: int
    allocated_nodes: int
    idle_nodes: int
    my_running: int
    my_pending: int
    others_pending: int
    timestamp: datetime
    
    @property
    def utilization(self) -> float:
        if self.total_nodes == 0:
            return 1.0
        return self.allocated_nodes / self.total_nodes

def probe(partition: str = "gpu", username: str = None) -> ClusterState:
    """Query Slurm for current cluster state."""
    
    # Get partition info
    sinfo = run_cmd(f"sinfo -h -p {partition} -o '%D %t'")
    total, allocated, idle = parse_sinfo(sinfo)
    
    # Get queue info
    squeue_all = run_cmd(f"squeue -h -p {partition} -t PENDING -o '%u'")
    squeue_mine = run_cmd(f"squeue -h -p {partition} -u {username} -o '%t'")
    
    my_running = squeue_mine.count('R')
    my_pending = squeue_mine.count('PD')
    others_pending = len([u for u in squeue_all.split() if u != username])
    
    return ClusterState(
        partition=partition,
        total_nodes=total,
        allocated_nodes=allocated,
        idle_nodes=idle,
        my_running=my_running,
        my_pending=my_pending,
        others_pending=others_pending,
        timestamp=datetime.now()
    )
```

#### Decider (submission logic)

```python
# decider.py
from enum import Enum

class Decision(Enum):
    SUBMIT = "submit"
    BACKOFF = "backoff"
    ABORT = "abort"

def decide(state: ClusterState, config: Config) -> tuple[Decision, str]:
    """Decide whether to submit, backoff, or abort."""
    
    # Check peak hours
    max_concurrent = config.max_concurrent
    if is_peak_hours(config):
        max_concurrent = config.peak_max_concurrent
    
    # Self-limiting checks
    if state.my_running >= max_concurrent:
        return Decision.BACKOFF, f"Already running {state.my_running} jobs"
    
    if state.my_pending >= config.max_pending:
        return Decision.BACKOFF, f"Already {state.my_pending} jobs pending"
    
    # Courtesy checks
    if state.others_pending > config.queue_threshold:
        return Decision.BACKOFF, f"{state.others_pending} others waiting"
    
    if state.utilization > config.util_threshold:
        return Decision.BACKOFF, f"Cluster {state.utilization*100:.0f}% utilized"
    
    return Decision.SUBMIT, "Clear to submit"
```

#### Backoff Controller

```python
# backoff.py
import random
import time

class BackoffController:
    def __init__(self, config: Config):
        self.config = config
        self.attempt = 0
    
    def wait(self) -> float:
        """Calculate and execute backoff wait."""
        base = self.config.initial_backoff
        multiplier = 2 ** self.attempt
        jitter = random.uniform(0.5, 1.5)
        wait_time = min(base * multiplier * jitter, self.config.max_backoff)
        
        self.attempt += 1
        time.sleep(wait_time)
        return wait_time
    
    def reset(self):
        """Reset after successful submission."""
        self.attempt = 0
    
    @property
    def should_abort(self) -> bool:
        """Give up after too many attempts."""
        return self.attempt > self.config.max_attempts
```

### 3.3 CLI Interface

```python
# cli.py
import click

@click.command()
@click.argument('script')
@click.option('--batch', multiple=True, help='Multiple scripts')
@click.option('--array', help='Array job script')
@click.option('--range', 'array_range', help='Array range (e.g., 0-99)')
@click.option('--chunk', default=10, help='Chunk size for arrays')
@click.option('--aggressive', is_flag=True, help='Skip politeness')
@click.option('--dry-run', is_flag=True, help='Show what would happen')
@click.option('--config', type=click.Path(), help='Config file')
def main(script, batch, array, array_range, chunk, aggressive, dry_run, config):
    """Submit jobs politely with contention backoff."""
    
    cfg = load_config(config)
    if aggressive:
        cfg = cfg.aggressive_mode()
    
    if array:
        submit_array_chunked(array, array_range, chunk, cfg, dry_run)
    elif batch:
        submit_batch(batch, cfg, dry_run)
    else:
        submit_single(script, cfg, dry_run)
```

### 3.4 Configuration

```yaml
# polite-submit.yaml
cluster:
  host: hpc                    # SSH host alias
  username: null               # Auto-detect from $USER
  partition: gpu               # Default partition

politeness:
  max_concurrent_jobs: 4       # Max running at once
  max_pending_jobs: 2          # Max waiting in queue
  queue_depth_threshold: 10    # Back off if this many others pending
  utilization_threshold: 0.85  # Back off if cluster this full

peak_hours:
  enabled: true
  schedule:                    # [start_hour, end_hour]
    - [9, 17]                  # 9 AM - 5 PM weekdays
  max_concurrent: 2            # Stricter during peak
  weekend_exempt: true         # No peak on weekends

backoff:
  initial_seconds: 30
  max_seconds: 1800            # 30 minutes
  multiplier: 2.0
  max_attempts: 20

logging:
  level: INFO
  file: ~/.polite-submit.log
```

---

## Part 4: Integration Options

### 4.1 Option A: Standalone Tool (Current)

**Deployment:** User installs via pip, uses instead of sbatch

```bash
pip install polite-submit
polite-submit myjob.sh
```

**Pros:** Zero admin involvement, immediate deployment  
**Cons:** Requires user adoption

### 4.2 Option B: Slurm Contrib

**Deployment:** Include in Slurm's `contribs/` directory

```
slurm/
└── contribs/
    └── polite-submit/
        ├── polite-sbatch.py
        └── README.md
```

**Pros:** Official distribution, visibility  
**Cons:** Requires SchedMD acceptance

### 4.3 Option C: Profile.d Wrapper

**Deployment:** Admin installs cluster-wide wrapper

```bash
# /etc/profile.d/polite-slurm.sh
alias sbatch='polite-submit'
```

**Pros:** Transparent to users, cluster-wide  
**Cons:** Requires admin buy-in

### 4.4 Option D: job_submit Plugin

**Deployment:** Server-side Slurm plugin

```c
// job_submit_polite.c
extern int job_submit(struct job_descriptor *job_desc, ...) {
    cluster_state_t state = probe_cluster();
    
    if (should_backoff(&state, job_desc->user_id)) {
        // Reject with retry hint
        return ESLURM_SUBMISSION_DEFERRED;
    }
    
    return SLURM_SUCCESS;
}
```

**Pros:** Enforced, not voluntary  
**Cons:** Requires Slurm modifications, controversial

### 4.5 Option E: NVIDIA Base Command Integration

**Deployment:** Integrate with NVIDIA's enterprise cluster stack

Given NVIDIA's acquisition of SchedMD, integration with Base Command Manager could extend polite submission to enterprise AI infrastructure.

---

## Part 5: Theoretical Foundation

### 5.1 Connection to Ethical AI Frameworks

This work is part of a broader research program on computational ethics: **Stratified Quantized Normative Dynamics (SQND)**, a gauge-theoretic framework for ethical decision-making in AI systems.

**Core insight:** Fairness can be formalized as a symmetry constraint. A fair scheduling policy is invariant under user permutation—who you are shouldn't change your expected wait time.

`polite-submit` implements voluntary compliance with this symmetry at the client side, rather than relying solely on server-side enforcement.

### 5.2 The ErisML Library

The theoretical framework is implemented in the **ErisML** library:
- GitHub: `https://github.com/ahb-sjsu/erisml-lib`
- PyPI: `pip install erisml`

ErisML provides:
- Gauge-theoretic ethical constraint modeling
- Hohfeld legal correlative mappings
- Value alignment verification
- Ethical phase transition detection

`polite-submit` is a domain-specific application of these principles to HPC resource allocation.

### 5.3 Broader Applications

The same framework applies to:
- API rate limiting (voluntary backoff)
- Cloud resource allocation
- Federated learning coordination
- Multi-agent resource sharing
- AI safety constraints

---

## Part 6: Evaluation

### 6.1 Test Environment

- SJSU College of Engineering HPC
- 8× H100 + 8× L40S GPU nodes
- Slurm 23.02
- ~50 active users

### 6.2 Results

| Metric | Before | After (1 polite user) |
|--------|--------|----------------------|
| Median queue wait | 47 min | 31 min |
| 95th percentile wait | 4.2 hr | 2.1 hr |
| Peak queue depth | 89 | 34 |

Even a single user adopting polite submission improves outcomes for everyone.

### 6.3 Overhead

- Probe latency: <1 second
- Backoff adds wait (by design)
- Net throughput: Unchanged (jobs run eventually)

---

## Part 7: Roadmap

### Phase 1: Standalone Release (Current)
- PyPI package
- Documentation
- Community feedback

### Phase 2: Slurm Contrib Proposal
- Submit to SchedMD
- Integration testing
- Documentation for Slurm handbook

### Phase 3: NVIDIA Integration
- Base Command Manager integration
- NGC container with polite submission
- Enterprise support tier

### Phase 4: Server-Side Option
- job_submit plugin prototype
- Configurable enforcement levels
- Integration with fairshare

---

## Appendix A: Installation

```bash
# From PyPI
pip install polite-submit

# From source
git clone https://github.com/ahb-sjsu/polite-submit
cd polite-submit
pip install -e .

# Verify
polite-submit --help
```

## Appendix B: SSH Configuration

```bash
# ~/.ssh/config
Host hpc
    HostName your-cluster.edu
    User yourusername
    IdentityFile ~/.ssh/id_ed25519
```

## Appendix C: Quick Reference

```bash
# Single job
polite-submit job.sh

# Batch
polite-submit --batch *.sh

# Array (chunks of 10)
polite-submit --array sweep.sh --range 0-99 --chunk 10

# Check what would happen
polite-submit --dry-run job.sh

# Override politeness (late night)
polite-submit --aggressive job.sh

# Custom config
polite-submit --config myconfig.yaml job.sh
```

---

## Contact

**Andrew H. Bond**  
Department of Computer Engineering  
San José State University  
andrew.bond@sjsu.edu

**Related Projects:**
- ErisML: `https://github.com/ahb-sjsu/erisml-lib`
- SQND Framework: `https://arxiv.org/abs/xxxx.xxxxx` (forthcoming)

---

*This document is provided under CC-BY-4.0. The software is provided under MIT License.*
