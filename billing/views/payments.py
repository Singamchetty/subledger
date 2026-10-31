from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .. import dependencies
from ..schemas import PaymentRecordSchema, PaymentResultSchema


class PaymentRecordView(APIView):
    @extend_schema(request=PaymentRecordSchema, responses={201: PaymentResultSchema})
    def post(self, request):
        data = PaymentRecordSchema.validated(request.data)
        attempt, invoice = dependencies.get_payment_service().record_payment(**data)
        body = PaymentResultSchema({"payment_attempt": attempt, "invoice": invoice}).data
        return Response(body, status=status.HTTP_201_CREATED)
