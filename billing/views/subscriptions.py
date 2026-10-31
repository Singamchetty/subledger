from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .. import dependencies
from ..schemas import (
    SubscriptionCreateSchema,
    SubscriptionFilterSchema,
    SubscriptionSchema,
)


class SubscriptionListCreateView(APIView):
    @extend_schema(request=SubscriptionCreateSchema, responses={201: SubscriptionSchema})
    def post(self, request):
        data = SubscriptionCreateSchema.validated(request.data)
        subscription = dependencies.get_subscription_service().create_subscription(**data)
        return Response(SubscriptionSchema(subscription).data, status=status.HTTP_201_CREATED)

    @extend_schema(responses=SubscriptionSchema(many=True))
    def get(self, request):
        params = SubscriptionFilterSchema.validated(request.query_params)
        subscriptions = dependencies.get_subscription_service().list_subscriptions(
            customer_id=params.get("customer_id"),
            status=params.get("status"),
        )
        return Response(SubscriptionSchema(subscriptions, many=True).data)


class SubscriptionCancelView(APIView):
    @extend_schema(request=None, responses=SubscriptionSchema)
    def patch(self, request, subscription_id):
        subscription = dependencies.get_subscription_service().cancel_subscription(subscription_id)
        return Response(SubscriptionSchema(subscription).data)
