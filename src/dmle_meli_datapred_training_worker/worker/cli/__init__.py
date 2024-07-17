from cis.runtime.cli.cli import main as cis_main
from dmle_meli_datapred_training_worker.worker.domain.worker import Worker


def main():
    """The main entry point of this worker in CIS."""
    cis_main(Worker)
