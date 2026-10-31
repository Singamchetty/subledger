from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .. import dependencies
from ..schemas import (
    CustomerCreateSchema,
    CustomerSchema,
    LedgerEntrySchema,
)


class CustomerListCreateView(APIView):
    @extend_schema(request=CustomerCreateSchema, responses={201: CustomerSchema})
    def post(self, request):
        data = CustomerCreateSchema.validated(request.data)
        customer = dependencies.get_customer_service().create_customer(data)
        return Response(CustomerSchema(customer).data, status=status.HTTP_201_CREATED)

    @extend_schema(responses=CustomerSchema(many=True))
    def get(self, request):
        customers = dependencies.get_customer_service().list_customers()
        return Response(CustomerSchema(customers, many=True).data)


class CustomerDetailView(APIView):
    @extend_schema(responses=CustomerSchema)
    def get(self, request, customer_id):
        customer = dependencies.get_customer_service().get_customer(customer_id)
        return Response(CustomerSchema(customer).data)


class CustomerLedgerView(APIView):
    @extend_schema(responses=LedgerEntrySchema(many=True))
    def get(self, request, customer_id):
        entries = dependencies.get_ledger_service().get_customer_ledger(customer_id)
        return Response(LedgerEntrySchema(entries, many=True).data)
