from pydantic import BaseModel


class ReportParams(BaseModel):
    """Body of a report creation request.

    A report covers every evaluation partition of the run, so it carries
    neither a split nor a user supplied name: its component and its run
    identify it.
    """

    run_id: int
    report_name: str
    parameters: dict = {}
