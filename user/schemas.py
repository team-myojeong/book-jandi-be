class Signup:
    def __init__(
            self,
            job_id: int | None = None,
            career_id: int | None = None,
            **kwargs
        ):
        self.job = job_id
        self.career = career_id
