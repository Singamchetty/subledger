from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .. import dependencies
from ..schemas import PlanCreateSchema, PlanSchema, PlanUpdateSchema


class PlanListCreateView(APIView):
    @extend_schema(request=PlanCreateSchema, responses={201: PlanSchema})
    def post(self, request):
        data = PlanCreateSchema.validated(request.data)
        plan = dependencies.get_plan_service().create_plan(data)
        return Response(PlanSchema(plan).data, status=status.HTTP_201_CREATED)

    @extend_schema(responses=PlanSchema(many=True))
    def get(self, request):
        plans = dependencies.get_plan_service().list_plans(request.query_params.get("status"))
        return Response(PlanSchema(plans, many=True).data)


class PlanDetailView(APIView):
    @extend_schema(request=PlanUpdateSchema, responses=PlanSchema)
    def patch(self, request, plan_id):
        changes = PlanUpdateSchema.validated(request.data)
        plan = dependencies.get_plan_service().update_plan(plan_id, changes)
        return Response(PlanSchema(plan).data)
