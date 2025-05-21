import argparse
import datetime
import os
from typing import List

from pipeline_mini.cfg import PipelineCfg
from pipeline_mini.jobs import extract_base_name, all_jobs, resubmit
from pipeline_mini.job_batch import JobBatch
from pipeline_mini.slurm import slurm_sacct, filter_latest_slurm_jobs


def start(cfg: PipelineCfg):
    slurm_jobs = slurm_sacct(run_id=cfg.run_id, start_date=cfg.start)
    slurm_jobs = filter_latest_slurm_jobs(slurm_jobs)

    all_batches = all_jobs(cfg)
    if cfg.submission == 1:
        submit_batches: List[JobBatch] = list(all_batches.values())
    else:
        submit_batches: List[JobBatch] = []
        for job in slurm_jobs:
            match job["state"]["current"][0]:
                case "FAILED":
                    submit_batches.append(all_batches[extract_base_name(job["name"])])
                case "COMPLETED":
                    pass
                case "RUNNING":  # Referencing itself
                    pass
                case _:
                    print(f"WARNING: Unrecognised state: {job['state']['current']}")

    job_ids = []
    for batch in submit_batches:
        job_ids.append(batch.submit())

    if job_ids:
        print("Resubmitting")
        resubmit(cfg, job_ids).submit()
    else:
        print("Pipeline Complete!")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--account", type=str, required=True, help="The account to associate jobs with.")
    parser.add_argument("--partition", type=str, required=True, help="The partition to associate jobs with.")
    parser.add_argument("--run_id", type=str, required=False, default=None, help="Custom Run ID")
    parser.add_argument("--work_dir", type=str, required=False, default=None, help="Working Directory")

    args = parser.parse_args()

    # Resolve run_id and work_dir, either from args or defaults
    run_id = args.run_id or datetime.datetime.now().strftime("%Y%m%d%H%M")
    work_dir = args.work_dir or os.getcwd()
    cfg_file = PipelineCfg.pipeline_cfg_file(work_dir, run_id)

    if os.path.exists(cfg_file):
        cfg = PipelineCfg.from_json(cfg_file)
        cfg.submission += 1  # Increment if we load from file
    else:
        cfg = PipelineCfg(
            run_id=run_id,
            work_dir=work_dir,
            start=datetime.datetime.now(),
            account=args.account,
            partition=args.partition,
            submission=1,
        )

    if cfg.submission > 3:
        raise RuntimeError("Too many submission, exiting...")

    start(cfg)

    cfg.to_json(cfg_file)


if __name__ == "__main__":
    main()
