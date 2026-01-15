# Client-Side Contention Management for Shared HPC Resources: A CSMA/CA-Inspired Approach

**Andrew H. Bond**  
Department of Computer Engineering  
San José State University  
andrew.bond@sjsu.edu

## Abstract

Shared high-performance computing (HPC) clusters face a tragedy of the commons: rational users maximize their own throughput by submitting large job batches, degrading service for others and creating queue congestion. While server-side schedulers like Slurm implement fairshare algorithms to mitigate this ex post, we propose a complementary client-side approach inspired by Carrier-Sense Multiple Access with Collision Avoidance (CSMA/CA) protocols from wireless networking. Our implementation, `polite-submit`, probes cluster state before job submission and implements exponential backoff when contention is detected, voluntarily yielding resources to other users. We frame this as an instance of a broader ethical resource allocation framework based on gauge-theoretic principles, where invariance under user permutation (fairness) emerges as a conserved quantity. Initial deployment at a university HPC facility demonstrates reduced queue wait times and improved user satisfaction without requiring scheduler modifications. The approach is particularly relevant as AI workloads increasingly dominate shared infrastructure.

**Keywords:** HPC, job scheduling, CSMA/CA, fairshare, ethical computing, resource allocation, Slurm

## 1. Introduction

The proliferation of GPU-accelerated computing for machine learning has intensified competition for shared HPC resources. A single user training large language models can consume entire GPU partitions for days, blocking dozens of other researchers. Server-side schedulers address this through fairshare priority algorithms that deprioritize heavy users over time [1], but these mechanisms are reactive—damage to queue health occurs before correction.

We propose a proactive, client-side approach: before submitting jobs, users probe cluster state and voluntarily defer when resources are congested. This mirrors the CSMA/CA protocol used in IEEE 802.11 wireless networks, where stations sense the medium before transmitting and back off exponentially upon detecting contention [2].

The contribution is twofold:
1. A practical tool (`polite-submit`) deployable without scheduler modifications
2. A theoretical framing connecting resource allocation ethics to gauge symmetry principles from physics

### 1.1 Motivation: The AI Compute Tragedy

Modern AI workloads exhibit characteristics that stress traditional scheduling:
- **Long duration**: Training runs span hours to weeks
- **High resource intensity**: 8-GPU nodes for single jobs
- **Bursty submission**: Hyperparameter sweeps submit hundreds of jobs simultaneously
- **Winner-take-all dynamics**: First to queue captures resources

A user submitting 100 GPU jobs at 9 AM Monday monopolizes the queue, even if fairshare eventually deprioritizes them. Other users experience immediate degradation while the scheduler "catches up."

### 1.2 The CSMA/CA Analogy

Wireless networks solved a similar problem. In early ALOHA protocols, stations transmitted at will, causing collisions and throughput collapse. CSMA/CA introduced:
1. **Carrier sensing**: Check if medium is busy before transmitting
2. **Collision avoidance**: Random backoff to desynchronize competing stations
3. **Exponential backoff**: Increase wait time upon repeated contention

We adapt these principles:

| Wireless (CSMA/CA) | HPC (polite-submit) |
|-------------------|---------------------|
| Sense carrier | Query `sinfo`, `squeue` |
| Medium busy | Utilization > threshold |
| Collision | Others pending in queue |
| Backoff | Delay next submission |
| Transmit | `sbatch` |

## 2. Design

### 2.1 Cluster State Probing

Before each job submission, `polite-submit` queries:
- **Partition utilization**: Fraction of nodes allocated
- **Queue depth**: Number of pending jobs from other users
- **Self-audit**: Own running and pending job counts

```python
def probe_cluster() -> ClusterState:
    utilization = allocated_nodes / total_nodes
    others_pending = count(pending_jobs) - count(my_pending_jobs)
    return ClusterState(utilization, others_pending, my_running, my_pending)
```

### 2.2 Submission Decision

A job is submitted only if:
1. Own running jobs < `MAX_CONCURRENT` (default: 4)
2. Own pending jobs < `MAX_PENDING` (default: 2)
3. Others pending < `QUEUE_DEPTH_THRESHOLD` (default: 10)
4. Utilization < `UTILIZATION_THRESHOLD` (default: 85%)

During peak hours (configurable), thresholds tighten further.

### 2.3 Exponential Backoff with Jitter

When conditions are not met, the client waits before retrying:

```
wait_time = min(base_backoff * (2 ^ attempt) * jitter, max_backoff)
```

Where `jitter ∈ [0.5, 1.5]` prevents synchronization among multiple polite clients. Initial backoff is 30 seconds; maximum is 30 minutes.

### 2.4 Adaptive Array Chunking

For job arrays (e.g., `--array=0-999`), the tool submits in small chunks (default: 10), probing cluster state between chunks. This prevents queue flooding while maintaining throughput during low-contention periods.

## 3. Theoretical Foundation: Gauge-Invariant Resource Allocation

We situate this work within a broader framework: Stratified Quantized Normative Dynamics (SQND), a gauge-theoretic approach to ethical decision-making in computational systems [3].

### 3.1 Fairness as Gauge Invariance

In physics, gauge invariance means that measurable quantities are unchanged under certain transformations. We propose an analogous principle for resource allocation:

**Definition (User Permutation Invariance):** A scheduling policy is *fair* if the expected wait time for a job is invariant under permutation of user identities.

Formally, let $W(j, u)$ denote wait time for job $j$ submitted by user $u$. Fairness requires:
$$W(j, u) = W(j, \pi(u)) \quad \forall \pi \in S_n$$

where $S_n$ is the symmetric group on $n$ users.

Standard fairshare scheduling approximates this over long time horizons, but instantaneous violations occur when a single user floods the queue.

### 3.2 Client-Side Compliance as Voluntary Symmetry Preservation

`polite-submit` implements voluntary compliance with fairness constraints. By limiting own submissions when others are waiting, a user preserves approximate user-permutation invariance *before* the scheduler must enforce it.

This is analogous to gauge fixing in physics: the underlying symmetry exists (fairshare will eventually restore balance), but voluntary compliance makes the symmetric state manifest at all times.

### 3.3 The Bond Index

We define a real-time metric for ethical resource usage:

$$B(u) = \frac{\text{resources consumed by } u}{\text{fair share of } u} \cdot \frac{\text{others waiting}}{\text{queue capacity}}$$

A Bond Index $B > 1$ indicates a user is consuming more than their fair share while others wait. `polite-submit` maintains $B \leq 1$ by construction.

## 4. Implementation

### 4.1 Architecture

```
┌─────────────────────────────────────────────┐
│           polite-submit client              │
├─────────────────────────────────────────────┤
│  ┌─────────┐  ┌──────────┐  ┌────────────┐  │
│  │ Prober  │→ │ Decider  │→ │ Submitter  │  │
│  └─────────┘  └──────────┘  └────────────┘  │
│       ↑            ↑                        │
│  ┌─────────┐  ┌──────────┐                  │
│  │ Config  │  │ Backoff  │                  │
│  │ (YAML)  │  │ State    │                  │
│  └─────────┘  └──────────┘                  │
└─────────────────────────────────────────────┘
         │ SSH
         ▼
┌─────────────────────────────────────────────┐
│        Slurm Cluster (unmodified)           │
│  sinfo, squeue, sbatch                      │
└─────────────────────────────────────────────┘
```

### 4.2 Configuration

```yaml
# polite-submit.yaml
politeness:
  max_concurrent_jobs: 4
  max_pending_jobs: 2
  queue_depth_threshold: 10
  utilization_threshold: 0.85

peak_hours:
  enabled: true
  hours: [[9, 17]]  # 9 AM - 5 PM
  max_concurrent: 2

backoff:
  initial_seconds: 30
  max_seconds: 1800
  multiplier: 2.0

weekend_aggressive: true
```

### 4.3 Usage

```bash
# Single job
polite-submit job.sh

# Batch submission
polite-submit --batch jobs/*.sh

# Array job in polite chunks
polite-submit --array sweep.sh --range 0-999 --chunk 10

# Late night, aggressive mode
polite-submit --aggressive job.sh
```

## 5. Evaluation

### 5.1 Deployment Environment

We deployed `polite-submit` on a university HPC cluster with:
- 8× NVIDIA H100 (80GB) GPU nodes
- 8× NVIDIA L40S (48GB) GPU nodes
- Slurm 23.02 with fairshare scheduling
- ~50 active users, predominantly ML researchers

### 5.2 Metrics

Over a 4-week observation period:

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Median queue wait (GPU) | 47 min | 31 min | -34% |
| 95th percentile wait | 4.2 hr | 2.1 hr | -50% |
| Queue depth peaks | 89 jobs | 34 jobs | -62% |
| User complaints | 7 | 1 | -86% |

Note: Only the author used `polite-submit` initially. Benefits accrued to *other* users from reduced queue pressure.

### 5.3 Overhead

Probing adds <1 second per submission. For batch jobs with inter-submission delays, overhead is negligible compared to job runtimes (typically hours).

## 6. Integration Pathways

### 6.1 Standalone Tool (Current)

Requires no cluster modifications. Users install locally and invoke instead of `sbatch`.

### 6.2 Slurm Plugin

A `job_submit` plugin could implement probing server-side, applying backoff before queue insertion. This requires cluster administrator cooperation.

### 6.3 Wrapper Script in `/etc/profile.d/`

Administrators could alias `sbatch` to a wrapper that invokes `polite-submit`, providing cluster-wide coverage without requiring user action.

### 6.4 Integration with NVIDIA Base Command

Following NVIDIA's acquisition of SchedMD, integration with NVIDIA's cluster management stack (Base Command, NGC) could extend polite submission to enterprise AI infrastructure.

## 7. Related Work

**Server-side fairshare**: Slurm's multifactor priority includes fairshare decay [1], but operates post-submission.

**Resource cgroups**: Linux cgroups limit resource consumption but don't address queue congestion.

**Kubernetes resource quotas**: Limit namespace consumption, analogous to our per-user caps [4].

**Game-theoretic scheduling**: Mechanism design approaches to truthful resource allocation [5] focus on server-side incentives rather than client-side compliance.

**Ethical AI frameworks**: Principled approaches to AI governance [6] have not addressed compute resource allocation specifically.

## 8. Future Work

1. **Multi-cluster federation**: Extend probing across federated Slurm clusters
2. **Learned backoff**: Reinforce backoff parameters from historical queue data
3. **Incentive integration**: Connect `polite-submit` usage to allocation priority (reward good citizens)
4. **SQND integration**: Implement full gauge-theoretic ethical reasoning for complex allocation decisions using the ErisML library [3]

## 9. Conclusion

Client-side contention management complements server-side scheduling, addressing queue health proactively rather than reactively. By framing resource allocation as a gauge symmetry problem, we connect practical tools to deeper principles of computational ethics. As AI workloads intensify competition for shared infrastructure, voluntary compliance mechanisms will become essential for sustainable research computing.

The `polite-submit` tool is available at: `https://github.com/ahb-sjsu/polite-submit`

## References

[1] Jette, M. A., & Grondona, M. (2003). SLURM: Simple Linux Utility for Resource Management. *Proceedings of ClusterWorld Conference*.

[2] IEEE 802.11 Working Group. (2016). IEEE Standard for Information Technology—Telecommunications and Information Exchange Between Systems—Local and Metropolitan Area Networks—Specific Requirements—Part 11.

[3] Bond, A. H. (2026). Stratified Quantized Normative Dynamics: A Gauge-Theoretic Framework for Ethical AI. *arXiv preprint*. (See also: ErisML library, `https://github.com/ahb-sjsu/erisml-lib`)

[4] Burns, B., Grant, B., Oppenheimer, D., Brewer, E., & Wilkes, J. (2016). Borg, Omega, and Kubernetes. *ACM Queue*, 14(1), 70-93.

[5] Nisan, N., & Ronen, A. (2001). Algorithmic mechanism design. *Games and Economic Behavior*, 35(1-2), 166-196.

[6] Jobin, A., Ienca, M., & Vayena, E. (2019). The global landscape of AI ethics guidelines. *Nature Machine Intelligence*, 1(9), 389-399.

---

## Appendix A: Quick Start

```bash
# Install
pip install polite-submit

# Configure SSH
echo "Host hpc
    HostName your-cluster.edu
    User yourusername" >> ~/.ssh/config

# Submit politely
polite-submit your_job.sh
```

## Appendix B: Algorithm Pseudocode

```
function POLITE_SUBMIT(job_script):
    backoff ← INITIAL_BACKOFF
    
    loop:
        state ← PROBE_CLUSTER()
        
        if state.my_running < MAX_CONCURRENT and
           state.my_pending < MAX_PENDING and
           state.others_pending < QUEUE_THRESHOLD and
           state.utilization < UTIL_THRESHOLD:
            
            result ← SBATCH(job_script)
            if result.success:
                return result.job_id
        
        wait_time ← backoff × RANDOM(0.5, 1.5)
        SLEEP(wait_time)
        backoff ← min(backoff × 2, MAX_BACKOFF)
```
