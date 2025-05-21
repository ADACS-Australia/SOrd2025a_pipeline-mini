import datetime
import json
import os


class PipelineCfg:
    def __init__(
        self, run_id: str, work_dir: str, start: datetime.datetime, account: str, partition: str, submission: int
    ):
        """Starting configuration of the pipeline

        :param run_id: The ID of this pipeline run. Independent of resubmissions
        :param work_dir: The working directory. Batch and out files stored here
        :param start: The starting time of the pipeline
        :param account: The account to attribute jobs to
        :param partition: The partition to attribute jobs to
        :param submission: The submission number - which run we're on. Increments on resubmission.
        """
        self.run_id = run_id
        self.work_dir = work_dir
        self.start = start
        self.account = account
        self.partition = partition
        self.submission = submission

        os.makedirs(os.path.join(self.work_dir, self.run_id), exist_ok=True)

    @classmethod
    def from_json(cls, path: str):
        with open(path) as f:
            data = json.load(f)
            data["start"] = datetime.datetime.fromisoformat(data["start"])
        return cls(**data)

    def to_json(self, path: str):
        obj = {
            "run_id": self.run_id,
            "work_dir": self.work_dir,
            "start": self.start.isoformat(),
            "account": self.account,
            "partition": self.partition,
            "submission": self.submission,
        }
        with open(path, "w") as f:
            json.dump(obj, f)

    @staticmethod
    def pipeline_cfg_file(work_dir: str, run_id: str) -> str:
        return os.path.join(work_dir, run_id, "pipeline_cfg.json")
