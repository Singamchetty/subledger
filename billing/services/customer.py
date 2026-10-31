from ..exceptions import ConflictError, NotFoundError


class CustomerService:
    def __init__(self, customer_repo):
        self.customer_repo = customer_repo

    def create_customer(self, data: dict):
        data = {**data, "email": data["email"].strip().lower()}
        if self.customer_repo.email_exists(data["email"]):
            raise ConflictError("A customer with this email already exists.")
        return self.customer_repo.create(**data)

    def list_customers(self):
        return self.customer_repo.list()

    def get_customer(self, customer_id: int):
        customer = self.customer_repo.get(customer_id)
        if customer is None:
            raise NotFoundError("Customer not found.")
        return customer
