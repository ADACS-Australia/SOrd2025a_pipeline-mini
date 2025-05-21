from datetime import timedelta
from dataclasses import dataclass
import subprocess
from typing import List


@dataclass
class JobBatch:
    batch_file: str
    commands: List[str]
    account: str
    partition: str
    time: timedelta
    job_name: str
    output: str
    memory_g: int
    ntasks: int = 1
    module_use: List[str] = None
    module_load: List[str] = None
    dependencies: List[str] = None

    def _format_timedelta(self) -> str:
        hours, remainder = divmod(self.time.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"

    def _generate_batch(self):
        module_use_str = ""
        if self.module_use:
            for m in self.module_use:
                module_use_str += f"module use {m}"
        module_load_str = ""
        if self.module_load:
            for m in self.module_load:
                module_load_str += f"module load {m}"
        time_str = self._format_timedelta()
        command_str = "\n".join(self.commands)
        dependency_str = f"#SBATCH --dependency=afterany:{','.join(self.dependencies)}" if self.dependencies else ""

        return f"""#!/bin/bash -l
#SBATCH --account={self.account}
#SBATCH --partition={self.partition}
#SBATCH --ntasks={self.ntasks}
#SBATCH --time={time_str}
#SBATCH --job-name={self.job_name}
#SBATCH --mem={self.memory_g}G
#SBATCH --export=NONE
#SBATCH --exclusive
#SBATCH --output={self.output}
{dependency_str}

{module_use_str}

{module_load_str}

{command_str}
"""

    def submit(self) -> str:
        """Creates the batch file and submits the job

        :return: The job ID
        """
        with open(self.batch_file, "w") as f:
            f.write(self._generate_batch())
        proc = subprocess.run(
            f"sbatch {self.batch_file}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        # Print to stdout so the supervisor can find the jobs
        print(proc.stdout.rstrip())

        if proc.returncode != 0:
            print(proc.stderr)
            raise RuntimeError(f"Error submitting batch file {self.batch_file}")

        job_id = proc.stdout.split()[-1]
        print(f"Successfully submitted '{self.job_name}' with Job ID: {job_id}")
        return job_id
