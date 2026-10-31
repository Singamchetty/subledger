from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .. import dependencies
from ..schemas import InvoiceGenerateSchema, InvoiceSchema


class InvoiceGenerateView(APIView):
    @extend_schema(request=InvoiceGenerateSchema, responses={201: InvoiceSchema})
    def post(self, request):
        data = InvoiceGenerateSchema.validated(request.data)
        invoice = dependencies.get_invoice_service().generate_invoice(
            data["subscription_id"], data.get("period_start"), data.get("period_end")
        )
        return Response(InvoiceSchema(invoice).data, status=status.HTTP_201_CREATED)


class InvoiceDetailView(APIView):
    @extend_schema(responses=InvoiceSchema)
    def get(self, request, invoice_id):
        invoice = dependencies.get_invoice_service().get_invoice(invoice_id)
        return Response(InvoiceSchema(invoice).data)
