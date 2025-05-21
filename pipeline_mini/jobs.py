from datetime import timedelta
import os
from typing import Dict, List

from pipeline_mini.job_batch import JobBatch
from pipeline_mini.cfg import PipelineCfg


def all_jobs(cfg: PipelineCfg) -> Dict[str, JobBatch]:
    """Get all of the job batches"""
    return {"job1": job1(cfg), "job2": job2(cfg)}


def gen_slurm_name(cfg: PipelineCfg, job_name: str) -> str:
    return f"{cfg.run_id}_{job_name}"


def extract_base_name(slurm_name: str) -> str:
    # Expected name format: ID_NAME
    return slurm_name.rsplit("_")[-1]


def gen_job_output(cfg: PipelineCfg, job_name: str) -> str:
    return os.path.join(cfg.work_dir, cfg.run_id, f"{job_name}_{cfg.submission}.out")


def gen_job_batch_name(cfg: PipelineCfg, job_name: str) -> str:
    return os.path.join(cfg.work_dir, cfg.run_id, f"{job_name}_{cfg.submission}.batch")


def job1(cfg: PipelineCfg):
    commands = ["echo 'sleeping for 10 seconds'", "sleep 10", "echo 'Done'"]
    return JobBatch(
        batch_file=gen_job_batch_name(cfg, "job1"),
        module_load=["singularity/4.1.0-slurm"],
        commands=commands,
        account=cfg.account,
        partition=cfg.partition,
        time=timedelta(minutes=2.0),
        job_name=gen_slurm_name(cfg, "job1"),
        output=gen_job_output(cfg, "job1"),
        memory_g=2,
    )


def job2(cfg: PipelineCfg):
    # Designed to fail on the first attempt, then succeed
    commands = ["echo 'sleeping for 10 seconds'", "sleep 10", f"[[ {cfg.submission} -eq 1 ]] && exit 1", "echo 'Done'"]
    return JobBatch(
        batch_file=gen_job_batch_name(cfg, "job2"),
        module_load=["singularity/4.1.0-slurm"],
        commands=commands,
        account=cfg.account,
        partition=cfg.partition,
        time=timedelta(minutes=2.0),
        job_name=gen_slurm_name(cfg, "job2"),
        output=gen_job_output(cfg, "job2"),
        memory_g=2,
    )


def resubmit(cfg: PipelineCfg, dependency_ids: List[int] = None):
    commands = [
        f"pipeline-mini --account {cfg.account} --partition {cfg.partition} --run_id {cfg.run_id} --work_dir {cfg.work_dir}"
    ]
    return JobBatch(
        batch_file=gen_job_batch_name(cfg, "resubmit"),
        module_use=["/software/projects/askaprt/ksmith1/modulefiles"],
        module_load=["pipeline-mini"],
        commands=commands,
        account=cfg.account,
        partition=cfg.partition,
        time=timedelta(minutes=5.0),
        job_name=gen_slurm_name(cfg, "resubmit"),
        output=gen_job_output(cfg, "resubmit"),
        memory_g=2,
        dependencies=dependency_ids,
    )
