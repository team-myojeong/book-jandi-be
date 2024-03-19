class Signup:
    def __init__(
            self,
            job_id: int | None = None,
            career_id: int | None = None,
            interest_list: list[int] = None,
            **kwargs
        ):
        self.job = job_id
        self.career = career_id
        self.interest1 = None
        self.interest2 = None
        self.interest3 = None

        for idx, interest_id in enumerate(interest_list if interest_list else []):
            setattr(self, f'interest{idx + 1}', interest_id)
