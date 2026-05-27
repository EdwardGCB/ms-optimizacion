from datetime import datetime

from bson import ObjectId
from bson.errors import InvalidId

from app.common.models.optimization import OptimizationModel
from app.common.enums.optimization_enum import TypeOptimizationEnum
from app.api.core.service_orchestrator.solvers.two_steps_solver import solve_two_steps
from app.api.core.service_orchestrator.solvers.graphical_solver import solve_graphical


class OptimizationProcess:

    _SOLVERS = {
        TypeOptimizationEnum.TWO_STEPS: solve_two_steps,
        TypeOptimizationEnum.GRAPHICAL: solve_graphical,
    }

    # -------------------------
    # Create
    # -------------------------
    async def create(self, payload):
        solver = self._SOLVERS.get(payload.type_optimization)
        if solver is None:
            return {
                "status": "error",
                "message": f"Método '{payload.type_optimization}' no soportado",
            }

        result = solver(payload)

        doc = OptimizationModel(
            payload=payload.model_dump(mode="json"),
            result=result,
            type_optimization=payload.type_optimization.value,
            created_at=datetime.utcnow(),
        )
        await doc.insert()

        return doc.model_dump(mode="json")

    # -------------------------
    # Get
    # -------------------------
    async def get(self, optimization_type: TypeOptimizationEnum, optimization_uuid: str):
        doc = await self._find_by_uuid(optimization_uuid)
        if not doc or doc.type_optimization != optimization_type.value:
            return "optimization not found"
        return doc.model_dump(mode="json")

    # -------------------------
    # Update
    # -------------------------
    async def update(self, optimization_uuid: str, payload):
        doc = await self._find_by_uuid(optimization_uuid)
        if not doc:
            return "optimization not found"

        new_payload = doc.payload.copy()
        new_payload.update(
            payload.model_dump(mode="json", exclude_none=True)
        )

        solver_key = new_payload.get("type_optimization")
        try:
            solver_enum = TypeOptimizationEnum(solver_key)
        except ValueError:
            return {
                "status": "error",
                "message": f"Método '{solver_key}' no soportado",
            }

        solver = self._SOLVERS.get(solver_enum)
        if solver is None:
            return {
                "status": "error",
                "message": f"Método '{solver_key}' no soportado",
            }

        from app.api.v1.serializer import CreateOptimizationRequest
        rebuilt = CreateOptimizationRequest(**new_payload)
        result = solver(rebuilt)

        doc.payload = new_payload
        doc.result = result
        doc.type_optimization = solver_enum.value
        await doc.save()

        return doc.model_dump(mode="json")

    # -------------------------
    # Delete
    # -------------------------
    async def delete(self, optimization_uuid: str):
        doc = await self._find_by_uuid(optimization_uuid)
        if not doc:
            return "optimization not found"

        await doc.delete()
        return "optimization deleted"

    # -------------------------
    # List
    # -------------------------
    async def list(self):
        docs = await OptimizationModel.find_all().to_list()
        return [d.model_dump(mode="json") for d in docs]

    # -------------------------
    # Helpers
    # -------------------------
    @staticmethod
    async def _find_by_uuid(optimization_uuid: str):
        try:
            object_id = ObjectId(optimization_uuid)
        except (InvalidId, TypeError):
            return None
        return await OptimizationModel.get(object_id)
